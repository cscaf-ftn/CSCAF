"""Load the curricula into the database, then segment and embed them for a run (two separate steps).

Step 1, `CurriculumLoader.load` (notebook data_load/02): the JSON files of a folder, top level only, each become one
`curriculum` row and one `syllabus` row per course. No segmentation happens here: a curriculum and its courses do
not belong to a run. Every course name and text is checked to be in English; a line that is not is printed as an
error with its language and recorded in the report, and does not stop the load.

Step 2, `CurriculumLoader.segment` (notebook data_load/03): every course of the named curricula without sentences for
the run is split by the text pipeline, every sentence is embedded, and the sentences are stored with their embeddings
and the run. A sentence whose text already occurs earlier in the same course is not stored again; a text repeated in
several courses is stored with each of them. `ord` is the position of a stored sentence within its course, from 1.

Step 1 skips a curriculum whose key is already in the database, and step 2 skips a course that already has sentences
for the run, so either can be resumed after an interruption.
"""
from __future__ import annotations

import json
from pathlib import Path

from cscaf.loading.curricula.curriculum_load_report import CurriculumLoadReport
from cscaf.loading.curricula.duplicate_courses import DuplicateCourses
from cscaf.storage.curriculum_sentence import CurriculumSentence
from cscaf.text.language_check import LanguageCheck


class CurriculumLoader:
    """Stores the curricula of a folder, then their sentences for a run."""

    def __init__(self, storage, text=None):
        self.storage = storage
        self.text = text

    @staticmethod
    def read(folder: Path) -> list[dict]:
        """Every `*.json` file directly in `folder` (no subfolders), sorted by file name."""
        documents = []
        for path in sorted(Path(folder).glob("*.json")):
            document = json.loads(path.read_text(encoding="utf-8"))
            if not document.get("curriculum_key"):
                raise ValueError(f"{path.name}: no curriculum_key")
            if not document.get("courses"):
                raise ValueError(f"{path.name}: no courses")
            documents.append(document)
        keys = [d["curriculum_key"] for d in documents]
        duplicates = sorted({k for k in keys if keys.count(k) > 1})
        if duplicates:
            raise ValueError(f"curriculum_key used by more than one file: {duplicates}")
        return documents

    @staticmethod
    def english_problems(document: dict) -> list[str]:
        """Every course name or text line of the document that is not in English, as a readable message."""
        problems = []
        for course in document["courses"]:
            for part, text in (("name", course["name"]), ("text", course.get("text") or "")):
                for line, language, content in LanguageCheck.non_english_lines(text):
                    problems.append(f"{document['curriculum_key']} / {course['name']} / {part} line {line}: "
                                    f"reads as {language}: {content[:120]}")
        return problems

    def _load_one(self, document: dict) -> dict:
        """Step 1 for one document: the curriculum row and its courses, without sentences. Returns counts.

        A course whose name and text are those of an earlier course in the same file is dropped before anything is
        stored; a repeated name with a different text is kept and reported.
        """
        key = document["curriculum_key"]
        document, duplicates = DuplicateCourses.drop(document)
        for dropped in duplicates["dropped"]:
            print(f"  {key}: course {dropped['name']!r} repeated with the same text, dropped")
        for kept in duplicates["same_name_other_text"]:
            print(f"  {key}: course {kept['name']!r} appears {len(kept['positions'])} times with different "
                  f"texts ({kept['lengths']} characters), all kept")
        not_english = self.english_problems(document)
        for problem in not_english:
            print(f"  ERROR not in English: {problem}")
        country = document["country"]["name"]
        country_id = self.storage.countries.country_id(country)
        if country_id is None:
            raise Exception(f"{key}: country {country!r} is not in the country table")

        curriculum_id = self.storage.curricula.save_curriculum(
            key, document["university_name"], document["faculty_name"], document["programme_name"],
            document["friendly_name"], document.get("short_name"), document.get("year"), country, country_id,
            document.get("edition"))
        if curriculum_id is None:
            raise Exception(f"Error saving curriculum {key}")

        counts = {"syllabi": 0, "not_english": not_english}
        for course in document["courses"]:
            syllabus_id = self.storage.curricula.save_syllabus(curriculum_id, key, course["name"], course.get("ects"),
                                                               course["text"])
            if syllabus_id is None:
                raise Exception(f"Error saving syllabus {key} / {course['name']}")
            counts["syllabi"] += 1
        return counts

    def load(self, folder: Path, report_folder: Path) -> CurriculumLoadReport:
        """Step 1 for every JSON file of the folder: curriculum and course rows only, with the English check."""
        folder = Path(folder)
        documents = self.read(folder)
        print(f"{len(documents)} curricula in {folder.name}")

        report = CurriculumLoadReport(source_folder=str(folder))
        for number, document in enumerate(documents, start=1):
            key = document["curriculum_key"]
            progress = f"[{number}/{len(documents)}] {key}"
            if self.storage.curricula.curriculum_id(key) is not None:
                print(f"{progress}: already in the database, skipped")
                report.add_skipped(key)
                continue
            counts = self._load_one(document)
            report.add_loaded(key, len(document["courses"]), counts)
            print(f"{progress}: {counts['syllabi']} syllabi"
                  + (f", {len(counts['not_english'])} lines NOT in English" if counts["not_english"] else ""))

        problems = report.verify(self.storage)
        path = report.write_report(report_folder, problems)
        totals = report.totals()
        print(f"loaded {totals['curricula_loaded']} curricula ({totals['curricula_skipped']} skipped), "
              f"{totals['syllabi']} syllabi, {totals['lines_not_english']} lines not in English")
        print("database check: " + ("counts agree" if not problems else "MISMATCH\n  " + "\n  ".join(problems)))
        print(f"report: {path.name}")
        return report

    def segment(self, run_id: str, curriculum_keys: list[str] | None = None, syllabi_per_batch: int = 40) -> dict:
        """Step 2: sentences with embeddings for every course of the named curricula that has none for the run.

        `curriculum_keys` names the curricula (None: every curriculum in the database); a key that is not in the
        database is an error.
        """
        syllabi = self.storage.curricula.syllabi_to_segment(run_id)
        if syllabi is None:
            raise Exception("Error reading the syllabi to segment")
        if curriculum_keys is not None:
            wanted = set(curriculum_keys)
            unknown = sorted(wanted - {key for _, key in self.storage.curricula.curricula() or []})
            if unknown:
                raise ValueError(f"not in the database: {unknown}")
            syllabi = [row for row in syllabi if row[2] in wanted]
        print(f"{len(syllabi)} syllabi to segment and embed for run {run_id}")
        if not syllabi:
            return {"syllabi": 0, "sentences": 0, "repeated": 0}

        embedding_dim = self.text.embedding_dimension
        embedding_dtype = self.text.embedding_dtype
        embedding_model = self.text.model_name
        counts = {"syllabi": 0, "sentences": 0, "repeated": 0}

        for start in range(0, len(syllabi), syllabi_per_batch):
            batch = syllabi[start:start + syllabi_per_batch]
            split_texts = self.text.sentences_many([text for _, _, _, _, text in batch])
            for (syllabus_id, _, key, name, _), sentences in zip(batch, split_texts):
                new_sentences, seen = [], set()
                for sentence in sentences:
                    if sentence in seen:
                        counts["repeated"] += 1
                        continue
                    seen.add(sentence)
                    new_sentences.append(sentence)
                counts["syllabi"] += 1
                if not new_sentences:
                    print(f"  {key} / {name}: no sentences")
                    continue
                embeddings = self.text.encode(new_sentences)
                records = [CurriculumSentence(None, order, syllabus_id, name, key, sentence, embedding,
                                              embedding_dim, embedding_dtype, embedding_model)
                           for order, (sentence, embedding) in enumerate(zip(new_sentences, embeddings), start=1)]
                stored = self.storage.curricula.save_sentences(records, run_id)
                if stored != len(records):
                    raise Exception(f"Error saving the sentences of {key} / {name}")
                counts["sentences"] += stored
            print(f"[{min(start + syllabi_per_batch, len(syllabi))}/{len(syllabi)}] syllabi, "
                  f"{counts['sentences']} sentences")
        return counts
