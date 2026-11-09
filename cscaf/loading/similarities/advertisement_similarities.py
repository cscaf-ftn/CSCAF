"""The similarity of every ECSF statement to every sentence of a run, and the best match of each statement.

Step 1 computes the cosine similarity of every pair (statement, sentence) from the stored embeddings and writes it to
the `_all` table of the source. The similarity is computed in float64 from the stored float32 vectors, each
normalised to unit length. Nothing is embedded again: the statements and the sentences must come from the same run,
hence the same embedding model.

Step 2 rebuilds the `_top_1` table (the best match of every statement in every curriculum or advertisement) from the
`_all` table by SQL and checks it against it. A curriculum or an advertisement that already has rows for the run is
skipped, so an interrupted computation can be resumed.
"""
from __future__ import annotations

from cscaf.loading.similarities.advertisement_similarity_report import AdvertisementSimilarityReport
from cscaf.loading.similarities.similarity_computation import SimilarityComputation
from cscaf.text.embedder import Embedder


class AdvertisementSimilarities(SimilarityComputation):
    """Every pair of every advertisement, then the best match of each statement in each advertisement."""

    ADS_PER_BATCH = 100
    SAMPLE_SIZE = 1000
    SAMPLE_SEED = 20260919
    SAMPLE_TOLERANCE = 1e-5

    def _compute_all(self, report: AdvertisementSimilarityReport, ads_per_batch: int = ADS_PER_BATCH) -> None:
        """Step 1: every pair of every advertisement that has no pairs yet."""
        run_id = self.run_id
        rf_ids, rf_matrix, rf_model = self._statements()
        ad_ids = self.storage.advertisements.ids_without_similarity(run_id)
        if ad_ids is None:
            raise Exception("Error reading the ads without similarity")
        print(f"{len(rf_ids)} ECSF statements ({rf_model}), {len(ad_ids)} ads to compute")

        for start in range(0, len(ad_ids), ads_per_batch):
            batch = ad_ids[start:start + ads_per_batch]
            loaded = self.storage.advertisements.sentence_embeddings(run_id, batch)
            if loaded is None:
                raise Exception("Error reading the ad sentences")
            sentences, sentence_matrix, model = loaded
            if model != rf_model or sentence_matrix.shape[1] != rf_matrix.shape[1]:
                raise Exception(f"ad sentences embedded with {model} ({sentence_matrix.shape[1]} dims), "
                                f"ECSF statements with {rf_model} ({rf_matrix.shape[1]} dims)")
            matrix = self.cosine_similarity_matrix(rf_matrix, sentence_matrix)
            rows = [(sentence_id, rf_id, float(matrix[i, j]))
                    for j, (sentence_id, _) in enumerate(sentences)
                    for i, rf_id in enumerate(rf_ids)]
            stored = self.storage.similarities.save_advertisement_similarities(rows)
            if stored != len(rows):
                raise Exception(f"Error saving the pairs of ads {batch[0]} to {batch[-1]}")
            report.ads += len(batch)
            report.sentences += len(sentences)
            report.pairs += stored
            print(f"[{min(start + ads_per_batch, len(ad_ids))}/{len(ad_ids)}] ads, {report.pairs} pairs")

    def _check(self, report: AdvertisementSimilarityReport) -> list[str]:
        """Completeness and agreement of the two tables, and an independent recomputation of a sample."""
        check = self.storage.similarities.check_advertisement_best_matches(self.run_id)
        if check is None:
            raise Exception("Error checking the similarity tables")
        report.check = check
        problems = []
        if check["all_rows"] != check["statements"] * check["sentences"]:
            problems.append(f"_all: {check['all_rows']} rows, expected {check['statements']} x {check['sentences']}")
        if check["top_1_rows"] != check["statements"] * check["ads"]:
            problems.append(f"top_1: {check['top_1_rows']} rows, expected {check['statements']} x {check['ads']}")
        if check["not_max"]:
            problems.append(f"top_1: {check['not_max']} rows are not the maximum in _all")
        if check["wrong_sentence"]:
            problems.append(f"top_1: {check['wrong_sentence']} rows point to a sentence of another ad or run")

        sample = self.storage.similarities.advertisement_similarity_sample(self.run_id, self.SAMPLE_SIZE, self.SAMPLE_SEED)
        if sample is None:
            raise Exception("Error sampling the _all table")
        differences = [abs(score - Embedder.cosine(rf_vector, sentence_vector)) for score, rf_vector, sentence_vector in sample]
        worst = max(differences, default=0.0)
        report.sample = {"pairs": len(sample), "max_abs_difference": worst, "tolerance": self.SAMPLE_TOLERANCE}
        if worst > self.SAMPLE_TOLERANCE:
            problems.append(f"_all: a recomputed score differs by {worst:.2e} (tolerance {self.SAMPLE_TOLERANCE:.0e})")
        print(f"check: {check}")
        print(f"sample: {len(sample)} pairs recomputed, largest difference {worst:.2e}")
        return problems

    def compute(self, report_folder, top_1_only: bool = False) -> AdvertisementSimilarityReport:
        """Step 1 (unless `top_1_only`), step 2, the checks and the report."""
        print(f"run: {self.run_id}")
        report = AdvertisementSimilarityReport(run_id=self.run_id)
        if not top_1_only:
            self._compute_all(report)
        rows = self.storage.similarities.refresh_advertisement_best_matches(self.run_id)
        if rows is None:
            raise Exception("Error refreshing job_advertisement_rf_similarity_top_1")
        print(f"top_1: {rows} rows")
        problems = self._check(report)
        path = report.write_report(report_folder, problems)
        print(f"computed {report.ads} ads now: {report.sentences} sentences, {report.pairs} pairs")
        print("database check: " + ("tables complete and in agreement" if not problems
                                    else "MISMATCH\n  " + "\n  ".join(problems)))
        print(f"report: {path.name}")
        return report
