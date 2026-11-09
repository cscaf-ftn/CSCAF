"""The report of the curriculum similarity computation."""
from __future__ import annotations

from dataclasses import dataclass, field

from cscaf.loading.load_report import LoadReport


@dataclass
class CurriculumSimilarityReport(LoadReport):
    """The pairs stored per curriculum, checked against the database."""

    run_id: str
    started_at: str = field(default_factory=LoadReport.now)
    curricula: list[dict] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    top_1: dict = field(default_factory=dict)

    def add_computed(self, key: str, curriculum_id: int, statements: int, sentences: int, stored: int) -> None:
        self.curricula.append({"curriculum_key": key, "curriculum_id": curriculum_id, "statements": statements,
                               "sentences": sentences, "pairs_expected": statements * sentences, "pairs": stored})

    def add_skipped(self, key: str) -> None:
        self.skipped.append(key)

    def totals(self) -> dict:
        return {"curricula_computed": len(self.curricula), "curricula_skipped": len(self.skipped),
                "sentences": sum(c["sentences"] for c in self.curricula),
                "pairs": sum(c["pairs"] for c in self.curricula)}

    def verify(self, storage) -> list[str]:
        problems = []
        for c in self.curricula:
            c["pairs_in_db"] = storage.similarities.count_curriculum_similarities(c["curriculum_id"], self.run_id)
            if not c["pairs"] == c["pairs_expected"] == c["pairs_in_db"]:
                problems.append(f"{c['curriculum_key']}: expected {c['pairs_expected']} pairs, stored {c['pairs']}, "
                                f"database holds {c['pairs_in_db']}")
        return problems

    def _stem(self) -> str:
        return f"curriculum_rf_similarity_{self.run_id}"

    def _content(self, problems: list[str], finished_at: str) -> dict:
        return {"run_id": self.run_id, "started_at": self.started_at, "finished_at": finished_at,
                "totals": self.totals(), "verified": not problems, "problems": problems, "top_1": self.top_1,
                "skipped": self.skipped, "curricula": self.curricula}
