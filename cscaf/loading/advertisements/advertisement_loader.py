"""Load the job advertisement export into the database, then segment and embed the advertisements for a run.

The input is `raw_data/job_advertisements/job_advertisements_full.json`: one record per advertisement with the columns
of `job_advertisement`. Step 1, `AdvertisementLoader.load` (notebook data_load/04), reads every advertisement, leaves
out those of countries outside the EU, removes duplicates and writes the snapshot and the remaining advertisements in
one transaction. Two advertisements are duplicates only if every field but the job key is identical (rule B3,
Section 3.2 of the paper); the rule is applied to the `content_hash` recorded when the advertisements were
collected, and the advertisement with the smallest job key is kept. A file whose checksum is already loaded is not
loaded again. Every title and description line is then checked to be in English.

Step 2, `AdvertisementLoader.segment` (notebook data_load/05): for every advertisement without sentences for the
run, the title and the description are split separately by the text pipeline, every sentence is embedded, and the
sentences are stored with their part (title or description). An identical sentence is stored once per
advertisement; `ord` numbers the stored sentences of an advertisement from 1, title first. Advertisements are written
in batches, one transaction per batch, so an interrupted run resumes with the advertisements still missing.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from cscaf.loading.advertisements.advertisement_load_report import AdvertisementLoadReport
from cscaf.loading.load_report import LoadReport
from cscaf.text.language_check import LanguageCheck


class AdvertisementLoader:
    """Stores the advertisements of the export, then their sentences for a run."""

    B3_FIELDS = ("date_posted", "date_posted_unix", "country", "location", "company", "title",
                 "title_before_translation", "description", "description_before_translation")
    DEDUP_RULE = ("B3: an ad is a duplicate only if every field but the crawler id is identical "
                  f"({', '.join(B3_FIELDS)}); the ad with the smallest job key is kept")
    ADS_PER_BATCH = 200

    def __init__(self, study, storage, text=None):
        self.study = study
        self.storage = storage
        self.text = text

    def _load_snapshot(self, path: Path, source_collection: str | None, report: AdvertisementLoadReport) -> int:
        """Step 1: EU advertisements of the export, without B3 duplicates, into the database. Returns the snapshot id."""
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        existing = self.storage.advertisements.snapshot_id(digest)
        if existing is not None:
            print(f"snapshot {path.name} is already loaded (id {existing}), skipped")
            report.snapshot = {"id": existing, "source_file": path.name, "source_sha256": digest,
                               "already_loaded": True, "n_loaded": self.storage.count_rows("job_advertisement")}
            return existing

        ads = self.read_export(path)
        countries = self.storage.countries.countries()
        if not countries:
            raise Exception("Error reading the country table")
        if len({ad["job_key"] for ad in ads}) != len(ads):
            raise ValueError(f"{path.name}: job keys are not unique")
        kept, left_out = self.select_ads(ads, countries)
        rows = []
        for ad, digest_b3, country_id in kept:
            values = self._normalised(ad)
            rows.append((ad["job_key"], country_id, values["country"], values["date_posted"], ad["date_posted_unix"],
                         ad.get("location") or None, ad["company"], ad["title"], ad["title_before_translation"],
                         ad["description"], ad["description_before_translation"], digest_b3))
        snapshot = {"created_at": LoadReport.now(), "source_file": path.name,
                    "source_sha256": digest, "source_collection": source_collection, "n_in_file": len(ads),
                    "n_not_eu": sum(left_out["not_eu"].values()), "n_duplicates_removed": len(left_out["duplicates"]),
                    "n_loaded": len(rows), "dedup_rule": self.DEDUP_RULE, "notes": None}
        snapshot_id = self.storage.advertisements.save_snapshot(snapshot, rows)
        if snapshot_id is None:
            raise Exception(f"Error saving snapshot {path.name}")

        report.snapshot = {"id": snapshot_id, **snapshot}
        report.left_out = left_out
        report.ads_per_country = dict(sorted(Counter(row[2] for row in rows).items()))
        dates = sorted(row[3] for row in rows)
        report.date_range = {"first": dates[0], "last": dates[-1]}
        print(f"snapshot {path.name}: {len(ads)} ads in the file, {snapshot['n_not_eu']} outside the EU "
              f"{left_out['not_eu']}, {snapshot['n_duplicates_removed']} B3 duplicates, {len(rows)} loaded "
              f"(posted {dates[0]} to {dates[-1]})")
        if left_out["eu_countries_without_ads"]:
            print(f"EU countries without ads: {left_out['eu_countries_without_ads']}")
        for group in left_out["identical_now_kept"]:
            print(f"  NOTE identical now, different when collected, all kept: {group}")
        return snapshot_id

    def english_problems(self) -> list[dict]:
        """Every advertisement title and description line in the database that is not in English."""
        ads = self.storage.advertisements.texts()
        if ads is None:
            raise Exception("Error reading the ads")
        problems = []
        for ad_id, job_key, title, description in ads:
            for part, text in (("title", title or ""), ("description", description or "")):
                for line, language, content in LanguageCheck.non_english_lines(text):
                    problems.append({"ad_id": ad_id, "job_key": job_key, "part": part, "line": line,
                                     "language": language, "text": content})
        return problems

    def _segment_and_embed(self, run_id: str, report: AdvertisementLoadReport,
                           ads_per_batch: int = ADS_PER_BATCH) -> None:
        """Step 2: sentences with embeddings for every advertisement that has none for `run_id`."""
        ads = self.storage.advertisements.to_segment(run_id)
        if ads is None:
            raise Exception("Error reading the ads to segment")
        print(f"{len(ads)} ads to segment and embed")
        embedding_dim = self.text.embedding_dimension
        embedding_dtype = self.text.embedding_dtype
        embedding_model = self.text.model_name

        for start in range(0, len(ads), ads_per_batch):
            batch = ads[start:start + ads_per_batch]
            parts = self.text.sentences_many([text for _, _, title, description in batch
                                              for text in (title, description)])
            pending = []
            for index, (ad_id, job_key, _, _) in enumerate(batch):
                seen, order = set(), 0
                for part, sentences in (("title", parts[2 * index]), ("description", parts[2 * index + 1])):
                    for sentence in sentences:
                        if sentence in seen:
                            report.repeated += 1
                            continue
                        seen.add(sentence)
                        order += 1
                        pending.append((order, ad_id, job_key, part, sentence))
                if order == 0:
                    report.ads_without_sentences.append(job_key)
            embeddings = self.text.encode([row[4] for row in pending]) if pending else []
            rows = [(*row, embedding, embedding_dim, embedding_dtype, embedding_model)
                    for row, embedding in zip(pending, embeddings)]
            stored = self.storage.advertisements.save_sentences(rows, run_id)
            if stored != len(rows):
                raise Exception(f"Error saving the sentences of ads {batch[0][1]} to {batch[-1][1]}")
            report.ads_segmented += len(batch)
            report.sentences += stored
            for row in pending:
                report.sentences_by_part[row[3]] += 1
            print(f"[{min(start + ads_per_batch, len(ads))}/{len(ads)}] ads, {report.sentences} sentences")

    def load(self, path: Path, report_folder: Path, source_collection: str | None = None) -> AdvertisementLoadReport:
        """Step 1 and the English check, the check against the database and the report. No segmentation."""
        report = AdvertisementLoadReport()
        self._load_snapshot(Path(path), source_collection, report)
        report.not_english = self.english_problems()
        for problem in report.not_english:
            print(f"  ERROR not in English: ad {problem['ad_id']} {problem['part']} line {problem['line']} "
                  f"reads as {problem['language']}: {problem['text'][:110]}")
        problems = report.verify(self.storage)
        written = report.write_report(report_folder, problems)
        print(f"{len(report.not_english)} lines not in English in "
              f"{len({p['ad_id'] for p in report.not_english})} ads")
        print("database check: " + ("counts agree" if not problems else "MISMATCH\n  " + "\n  ".join(problems)))
        print(f"report: {written.name}")
        return report

    def segment(self, report_folder: Path) -> AdvertisementLoadReport:
        """Step 2 for every advertisement without sentences for the run, the check and the report."""
        run_id = self.storage.runs.ensure_run(self.study.run_record())
        if run_id is None:
            raise Exception("Error saving the run")
        print(f"run: {run_id}")
        report = AdvertisementLoadReport(run_id=run_id)
        self._segment_and_embed(run_id, report)
        problems = report.verify(self.storage)
        written = report.write_report(report_folder, problems)
        print(f"segmented {report.ads_segmented} ads: {report.sentences} sentences {report.sentences_by_part}, "
              f"{report.repeated} repeated within an ad, not stored; {len(report.ads_without_sentences)} ads "
              f"without any sentence")
        print("database check: " + ("counts agree" if not problems else "MISMATCH\n  " + "\n  ".join(problems)))
        print(f"report: {written.name}")
        return report

    @staticmethod
    def read_export(path: Path) -> list[dict]:
        """The advertisements of the export file, each a dict of `job_advertisement` columns."""
        data = json.loads(path.read_text(encoding="utf-8"))
        ads = data["advertisements"] if isinstance(data, dict) else data
        if not isinstance(ads, list) or not all(isinstance(ad, dict) and ad.get("job_key") for ad in ads):
            raise ValueError(f"{path.name} is not a list of advertisements with a job key")
        return ads

    @staticmethod
    def _normalised(ad: dict) -> dict:
        """The B3 fields in the form they are stored: country without spaces, date as ISO date, no None."""
        values = {name: ad.get(name) for name in AdvertisementLoader.B3_FIELDS}
        values.update(country=ad["country"].strip(), date_posted=str(ad["date_posted"])[:10], location=ad.get("location") or "")
        return values

    @staticmethod
    def content_hash(ad: dict) -> str:
        """SHA-256 of the B3 fields; equal hashes mean duplicates under rule B3."""
        return hashlib.sha256(json.dumps(AdvertisementLoader._normalised(ad), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

    @staticmethod
    def recorded_hash(ad: dict) -> str:
        """The B3 hash recorded when the advertisement was collected, or the hash of its current fields."""
        return ad.get("content_hash") or AdvertisementLoader.content_hash(ad)

    @staticmethod
    def identical_now(ads: list[dict]) -> list[list[str]]:
        """Job keys of advertisements whose current B3 fields are identical although their recorded hashes differ."""
        groups = defaultdict(list)
        for ad in ads:
            groups[AdvertisementLoader.content_hash(ad)].append(ad)
        return [sorted(ad["job_key"] for ad in group) for group in groups.values()
                if len(group) > 1 and len({AdvertisementLoader.recorded_hash(ad) for ad in group}) > 1]

    @staticmethod
    def select_ads(ads: list[dict], countries: list[tuple[int, str, bool]]) -> tuple[list, dict]:
        """Keep the advertisements of EU countries and remove B3 duplicates. Returns (kept, what was left out)."""
        eu = {name: country_id for country_id, name, is_eu in countries if is_eu}
        not_eu = Counter(ad["country"].strip() for ad in ads if ad["country"].strip() not in eu)
        groups = defaultdict(list)
        for ad in ads:
            if ad["country"].strip() in eu:
                groups[AdvertisementLoader.recorded_hash(ad)].append(ad)
        kept, duplicates = [], []
        for digest, group in groups.items():
            group.sort(key=lambda ad: ad["job_key"])
            kept.append((group[0], digest, eu[group[0]["country"].strip()]))
            duplicates += [{"removed": ad["job_key"], "kept": group[0]["job_key"]} for ad in group[1:]]
        kept.sort(key=lambda item: item[0]["job_key"])
        return kept, {"not_eu": dict(sorted(not_eu.items())), "duplicates": duplicates,
                      "identical_now_kept": AdvertisementLoader.identical_now([item[0] for item in kept]),
                      "eu_countries_without_ads": sorted(set(eu) - {ad["country"].strip() for ad in ads})}
