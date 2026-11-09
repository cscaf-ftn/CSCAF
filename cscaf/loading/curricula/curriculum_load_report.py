"""The report of a curriculum load."""
from __future__ import annotations

from dataclasses import dataclass, field

from cscaf.loading.load_report import LoadReport


@dataclass
class CurriculumLoadReport(LoadReport):
    """The curricula and courses step 1 stored, checked against the database."""

    source_folder: str
    started_at: str = field(default_factory=LoadReport.now)
    curricula: list[dict] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def add_loaded(self, key: str, courses_in_file: int, counts: dict) -> None:
        self.curricula.append({"curriculum_key": key, "courses_in_file": courses_in_file, **counts})

    def add_skipped(self, key: str) -> None:
        self.skipped.append(key)

    def totals(self) -> dict:
        return {"curricula_loaded": len(self.curricula),
                "curricula_skipped": len(self.skipped),
                "courses_in_file": sum(c["courses_in_file"] for c in self.curricula),
                "syllabi": sum(c["syllabi"] for c in self.curricula),
                "lines_not_english": sum(len(c["not_english"]) for c in self.curricula)}

    def verify(self, storage) -> list[str]:
        """Compare the counts with the database; return the mismatches (empty if all agree)."""
        problems = []
        for c in self.curricula:
            in_db = storage.curricula.content_counts(c["curriculum_key"], "") or {}
            c["syllabi_in_db"] = in_db.get("syllabi")
            if c["syllabi"] != c["courses_in_file"]:
                problems.append(f"{c['curriculum_key']}: {c['courses_in_file']} courses in the file, "
                                f"{c['syllabi']} syllabi stored")
            if c["syllabi_in_db"] != c["syllabi"]:
                problems.append(f"{c['curriculum_key']}: logged {c['syllabi']} syllabi, "
                                f"database holds {c['syllabi_in_db']}")
        return problems

    def _stem(self) -> str:
        return "curriculum_load"

    def _content(self, problems: list[str], finished_at: str) -> dict:
        return {"source_folder": self.source_folder, "started_at": self.started_at, "finished_at": finished_at,
                "totals": self.totals(), "verified": not problems, "problems": problems, "skipped": self.skipped,
                "curricula": self.curricula}
