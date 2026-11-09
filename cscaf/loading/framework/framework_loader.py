"""Load a reference framework into the database: its roles, subsections and statements with their embeddings."""
from __future__ import annotations

from cscaf.framework.reference_framework import ReferenceFramework


class FrameworkLoader:
    """Stores every profile, its two subsections and its statements, each statement embedded once."""

    def __init__(self, study, storage, text):
        self.study = study
        self.storage = storage
        self.text = text

    def load(self, framework: ReferenceFramework) -> dict:
        """Store the framework; returns the counts, for the caller to check against the release."""
        profiles = framework.profiles()
        run_id = self.storage.runs.ensure_run(self.study.run_record())
        if run_id is None:
            raise Exception("Error saving the run")
        print(f"run: {run_id}")

        dimension = self.text.embedding_dimension
        dtype = self.text.embedding_dtype
        model = self.text.model_name
        stored: dict[str, int] = {}
        counts = {"sections": 0, "subsections": 0, "rows": 0}

        for profile in profiles:
            title = profile["title"]
            short_name = framework.short_name(title)
            section_id = self.storage.framework.save_section(short_name, title)
            if section_id is None:
                raise Exception(f"Error saving section {title}")
            counts["sections"] += 1
            for subsection, field in framework.SUBSECTIONS:
                statements = profile[field]
                if not statements:
                    raise Exception(f"{title} has no {field}")
                subsection_id = self.storage.framework.save_subsection(subsection, section_id)
                if subsection_id is None:
                    raise Exception(f"Error saving subsection {subsection} of {title}")
                counts["subsections"] += 1
                for order, statement in enumerate(statements, start=1):
                    statement = statement.strip()
                    if statement not in stored:
                        embedding = self.text.encode([statement])[0]
                        if embedding is None:
                            raise Exception(f"Error embedding: {statement}")
                        statement_id = self.storage.framework.save_statement(statement, embedding, dimension, dtype,
                                                                              model, run_id)
                        if statement_id is None:
                            raise Exception(f"Error saving: {statement}")
                        stored[statement] = statement_id
                    if self.storage.framework.save_subsection_statement(subsection_id, stored[statement], order) is None:
                        raise Exception(f"Error linking {statement} to {title} / {subsection}")
                    counts["rows"] += 1
            print(f"  {short_name:18s} {len(profile['key_skills']):2d} skills, "
                  f"{len(profile['key_knowledge']):2d} knowledge")

        counts["statements"] = len(stored)
        counts["view_rows"] = self.storage.framework.refresh_statement_view()
        print(f"stored {counts['sections']} profiles, {counts['rows']} role-statement rows, "
              f"{counts['statements']} distinct statements; view_rf_sentences: {counts['view_rows']} rows")
        return counts
