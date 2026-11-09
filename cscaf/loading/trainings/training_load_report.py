"""The report of an industry training load."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TrainingLoadReport:
    """What a load did, printed by the notebook."""

    loaded: list[dict] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    roles_replaced: list[dict] = field(default_factory=list)
    sentences: int = 0
    similarities: int = 0
    top_1_rows: int = 0

    def as_dict(self) -> dict:
        return {"loaded": self.loaded, "skipped": self.skipped, "roles_replaced": self.roles_replaced,
                "sentences": self.sentences, "similarities": self.similarities, "top_1_rows": self.top_1_rows}
