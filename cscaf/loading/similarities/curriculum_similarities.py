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

from cscaf.loading.similarities.curriculum_similarity_report import CurriculumSimilarityReport
from cscaf.loading.similarities.similarity_computation import SimilarityComputation


class CurriculumSimilarities(SimilarityComputation):
    """Every pair of every curriculum, then the best matches per curriculum and per course."""

    def _compute_curriculum(self, rf_ids, rf_matrix, rf_model, curriculum_id: int, curriculum_key: str) -> tuple:
        """Compute and store every pair of one curriculum. Returns (sentences, rows stored)."""
        run_id = self.run_id
        loaded = self.storage.curricula.sentence_embeddings(curriculum_key, run_id)
        if loaded is None:
            raise Exception(f"Error reading the sentences of {curriculum_key}")
        sentences, sentence_matrix, model = loaded
        if not sentences:
            raise Exception(f"{curriculum_key} has no sentences for run {run_id}")
        if model != rf_model or sentence_matrix.shape[1] != rf_matrix.shape[1]:
            raise Exception(f"{curriculum_key}: sentences embedded with {model} ({sentence_matrix.shape[1]} dims), "
                            f"ECSF statements with {rf_model} ({rf_matrix.shape[1]} dims)")
        matrix = self.cosine_similarity_matrix(rf_matrix, sentence_matrix)
        rows = [(run_id, rf_id, sentence_id, float(matrix[i, j]), curriculum_id, curriculum_key, syllabus_id,
                 syllabus_name)
                for j, (sentence_id, syllabus_id, syllabus_name) in enumerate(sentences)
                for i, rf_id in enumerate(rf_ids)]
        stored = self.storage.similarities.save_curriculum_similarities(rows)
        if stored != len(rows):
            raise Exception(f"Error saving the pairs of {curriculum_key}")
        return len(sentences), stored

    def refresh_best_matches(self) -> tuple[dict, list[str]]:
        """Step 2: rebuild the top_1 table of the run from the _all table and check it. Returns (counts, problems)."""
        rows = self.storage.similarities.refresh_curriculum_best_matches(self.run_id)
        if rows is None:
            raise Exception("Error refreshing curriculum_rf_similarity_top_1")
        check = self.storage.similarities.check_curriculum_best_matches(self.run_id)
        if check is None:
            raise Exception("Error checking curriculum_rf_similarity_top_1")
        problems = []
        if check["primary_rows"] != check["pairs_in_all"]:
            problems.append(f"top_1: {check['primary_rows']} primary rows for {check['pairs_in_all']} pairs in _all")
        if check["primary_not_max"]:
            problems.append(f"top_1: {check['primary_not_max']} primary rows are not the maximum in _all")
        if check["other_text"]:
            problems.append(f"top_1: {check['other_text']} rows differ in text from their primary row")
        print(f"top_1: {check['rows']} rows, {check['primary_rows']} primary "
              f"({check['rows'] - check['primary_rows']} more courses with the same text); "
              + ("agrees with _all" if not problems else "MISMATCH\n  " + "\n  ".join(problems)))
        return check, problems

    def compute(self, report_folder, curriculum_keys: list[str] | None = None) -> CurriculumSimilarityReport:
        """Step 1 for the named curricula (None: every curriculum), step 2, the best matches per course, the checks
        and the report. The top_1 tables are rebuilt for the whole run."""
        run_id = self.run_id
        print(f"run: {run_id}")
        rf_ids, rf_matrix, rf_model = self._statements()
        curricula = self.storage.curricula.curricula()
        if not curricula:
            raise Exception("No curricula in the database")
        if curriculum_keys is not None:
            wanted = set(curriculum_keys)
            unknown = sorted(wanted - {key for _, key in curricula})
            if unknown:
                raise ValueError(f"not in the database: {unknown}")
            curricula = [(curriculum_id, key) for curriculum_id, key in curricula if key in wanted]
        print(f"{len(rf_ids)} ECSF statements ({rf_model}), {len(curricula)} curricula")

        report = CurriculumSimilarityReport(run_id=run_id)
        for number, (curriculum_id, key) in enumerate(curricula, start=1):
            progress = f"[{number}/{len(curricula)}] {key}"
            existing = self.storage.similarities.count_curriculum_similarities(curriculum_id, run_id)
            if existing:
                print(f"{progress}: {existing} pairs already in the database, skipped")
                report.add_skipped(key)
                continue
            sentences, stored = self._compute_curriculum(rf_ids, rf_matrix, rf_model, curriculum_id, key)
            report.add_computed(key, curriculum_id, len(rf_ids), sentences, stored)
            print(f"{progress}: {sentences} sentences x {len(rf_ids)} statements = {stored} pairs")

        problems = report.verify(self.storage)
        report.top_1, top_1_problems = self.refresh_best_matches()
        problems += top_1_problems
        syllabus_rows = self.storage.similarities.refresh_course_best_matches(run_id)
        if syllabus_rows is None:
            raise Exception("Error refreshing curriculum_syllabus_rf_top_1")
        report.top_1["syllabus_top_1_rows"] = syllabus_rows
        print(f"curriculum_syllabus_rf_top_1: {syllabus_rows} rows")
        path = report.write_report(report_folder, problems)
        totals = report.totals()
        print(f"computed {totals['curricula_computed']} curricula ({totals['curricula_skipped']} skipped), "
              f"{totals['pairs']} pairs")
        print("database check: " + ("counts agree" if not problems else "MISMATCH\n  " + "\n  ".join(problems)))
        print(f"report: {path.name}")
        return report
