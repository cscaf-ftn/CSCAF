"""The report of the advertisement similarity computation."""
from __future__ import annotations

from dataclasses import dataclass, field

from cscaf.loading.load_report import LoadReport


@dataclass
class AdvertisementSimilarityReport(LoadReport):
    """The pairs stored, the checks of the two tables and of a recomputed sample."""

    run_id: str
    started_at: str = field(default_factory=LoadReport.now)
    ads: int = 0
    sentences: int = 0
    pairs: int = 0
    check: dict = field(default_factory=dict)
    sample: dict = field(default_factory=dict)

    def _stem(self) -> str:
        return f"job_advertisement_rf_similarity_{self.run_id}"

    def _content(self, problems: list[str], finished_at: str) -> dict:
        return {"run_id": self.run_id, "started_at": self.started_at, "finished_at": finished_at,
                "verified": not problems, "problems": problems,
                "computed_now": {"ads": self.ads, "sentences": self.sentences, "pairs": self.pairs},
                "check": self.check, "sample": self.sample}
