"""Load the industry training courses, segment and embed them, and score them against the ECSF statements.

One JSON file per course (raw_data/training_courses) holds the course page as published, with the roles the provider
declares and one text per extraction variant. `TrainingLoader.load` (notebook data_load/06) stores one row per
(course, variant) with its declared roles; `segment` and `similarities` (notebook data_load/07) split and embed every
text and score every statement against every sentence. The texts are added to a curriculum by the course-addition
simulation of Section 4.2 of the paper.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from cscaf.loading.trainings.training_load_report import TrainingLoadReport
from cscaf.text.language_check import LanguageCheck


class TrainingLoader:
    """Stores the training courses of a folder, their sentences for a run and their similarities."""

    def __init__(self, study, storage, text=None):
        self.study = study
        self.storage = storage
        self.text = text

    @staticmethod
    def read(folder: Path) -> list[dict]:
        """The course files of a folder, one JSON file per course, ordered by course code.

        Raises:
            ValueError: a file lacks a field the load needs, or two files share a course code.
        """
        courses = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(Path(folder).glob("*.json"))]
        required = ("code", "title", "provider", "url", "accessed_date", "declared_roles", "variants")
        for course in courses:
            missing = [name for name in required if not course.get(name)]
            if missing:
                raise ValueError(f"{course.get('code', '?')}: missing {missing}")
            if not all(v.get("variant") and v.get("text") for v in course["variants"]):
                raise ValueError(f"{course['code']}: a variant without a name or a text")
        codes = [course["code"] for course in courses]
        if len(set(codes)) != len(codes):
            raise ValueError(f"course codes repeated in {folder}")
        return courses

    def load(self, folder: Path) -> TrainingLoadReport:
        """Store one row per (course, extraction variant), with the roles the provider declares.

        Raises:
            Exception: a role is not an ECSF role short name, or a row could not be written. The load stops rather
                than leaving a course partly loaded.
        """
        courses = self.read(folder)
        roles_in_db = self.storage.framework.role_short_names()
        unknown = sorted({role for course in courses for role in course["declared_roles"]} - roles_in_db)
        if unknown:
            raise Exception(f"not ECSF role short names: {unknown}; load the ECSF first")
        report = TrainingLoadReport()
        for course in courses:
            code, roles = course["code"], course["declared_roles"]
            stored = {tuple(t["roles"]) for t in (self.storage.trainings.trainings() or []) if t["code"] == code}
            if stored and stored != {tuple(sorted(roles))}:
                if self.storage.trainings.replace_roles(code, roles) is None:
                    raise Exception(f"Error replacing the roles of {code}")
                report.roles_replaced.append({"code": code, "before": sorted(stored), "after": sorted(roles)})
            for variant in course["variants"]:
                name = variant["variant"]
                if self.storage.trainings.training_id(code, name) is not None:
                    report.skipped.append(f"{code}/{name}")
                    continue
                training_id = self.storage.trainings.save_training({
                    "code": code, "title": course["title"],
                    "source_description": course["provider"], "source_url": course["url"],
                    "accessed_date": course["accessed_date"], "variant": name,
                    "sections_taken": variant["sections_taken"], "text": variant["text"],
                    "notes": course.get("role_in_study"), "roles": roles})
                if training_id is None:
                    raise Exception(f"Error storing {code}/{name}")
                report.loaded.append({"id": training_id, "code": code, "variant": name, "roles": roles,
                                      "characters": len(variant["text"]),
                                      "sections_taken": variant["sections_taken"].split(" | ")})
        return report

    def english_problems(self) -> list[tuple]:
        """Every line of a stored course text that is not in English: (code, variant, line, language, text)."""
        problems = []
        for code, variant, text in self.storage.trainings.texts():
            for line, language, content in LanguageCheck.non_english_lines(text):
                problems.append((code, variant, line, language, content))
        return problems

    def segment(self, run_id: str) -> dict:
        """Split and embed every stored course text that has no sentences for the run.

        A sentence whose text already occurs earlier in the same course text is not stored again, and `ord` counts the
        stored sentences from 1.

        Returns:
            {"courses", "sentences", "repeated", "dropped"}; `dropped` counts the units the cleaning rules removed
        """
        trainings = self.storage.trainings.trainings(run_id)
        if trainings is None:
            raise Exception("Error reading the industry trainings")
        embedding_dim = self.text.embedding_dimension
        embedding_dtype = self.text.embedding_dtype
        embedding_model = self.text.model_name

        courses = sentences_stored = repeated = dropped_units = 0
        for training in trainings:
            if training["sentences"]:
                continue
            text = self.storage.trainings.text(training["id"])
            if text is None:
                raise Exception(f"Error reading the text of {training['code']}/{training['variant']}")
            kept, dropped = self.text.sentences_with_dropped(text)
            dropped_units += len(dropped)
            unique = []
            for sentence in kept:
                if sentence in set(unique):
                    repeated += 1
                    continue
                unique.append(sentence)
            embeddings = self.text.encode(unique) if unique else []
            payload = [{"ord": index + 1, "industry_training_id": training["id"], "sentence": sentence,
                        "sentence_embedding": embeddings[index],
                        "embedding_dim": embedding_dim, "embedding_dtype": embedding_dtype,
                        "embedding_model": embedding_model}
                       for index, sentence in enumerate(unique)]
            if not payload:
                raise Exception(f"{training['code']}/{training['variant']} produced no sentence; the "
                                f"extraction or the cleaning rules removed everything")
            stored = self.storage.trainings.save_sentences(payload, run_id)
            if stored is None:
                raise Exception(f"Error storing the sentences of {training['code']}/{training['variant']}")
            courses += 1
            sentences_stored += stored
        return {"courses": courses, "sentences": sentences_stored, "repeated": repeated, "dropped": dropped_units}

    def similarities(self, run_id: str) -> dict:
        """Score every ECSF statement against every sentence of every course, then rebuild the top-1 table.

        The statements and the sentences are both unit-length vectors of the same run, so the score is their dot
        product, computed as stored (float32).

        Returns:
            {"courses", "pairs", "top_1_rows"}
        """
        statement_ids, statements, _ = self.storage.framework.statement_embeddings(run_id)
        if not len(statement_ids):
            raise Exception(f"no ECSF statement embeddings for run {run_id}")
        trainings = self.storage.trainings.trainings(run_id)
        if trainings is None:
            raise Exception("Error reading the industry trainings")

        courses = pairs = 0
        for training in trainings:
            if self.storage.similarities.count_training_similarities(run_id, training["id"]):
                continue
            rows, matrix, _ = self.storage.trainings.sentence_embeddings(training["id"], run_id)
            if not rows:
                raise Exception(f"{training['code']}/{training['variant']} has no sentences for {run_id}")
            scores = np.asarray(statements) @ np.asarray(matrix).T
            payload = [(run_id, int(statement_ids[i]), int(rows[j][0]), float(scores[i, j]),
                        int(training["id"]), training["code"])
                       for i in range(scores.shape[0]) for j in range(scores.shape[1])]
            stored = self.storage.similarities.save_training_similarities(payload)
            if stored is None:
                raise Exception(f"Error storing the similarities of {training['code']}")
            courses += 1
            pairs += stored
        top_1 = self.storage.similarities.refresh_training_best_matches(run_id)
        if top_1 is None:
            raise Exception("Error refreshing industry_training_rf_similarity_top_1")
        return {"courses": courses, "pairs": pairs, "top_1_rows": top_1}
