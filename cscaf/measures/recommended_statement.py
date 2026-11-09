"""One recommended statement (Section 4.2 of the paper)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecommendedStatement:
    """One statement the programme comes closest to covering without covering it."""

    rf_sentence_id: int
    statement: str
    subsection: str
    similarity: float
    distance_to_tau: float
    closest_sentence: str | None = None
    closest_course: str | None = None

    def as_dict(self) -> dict:
        return {"rf_sentence_id": self.rf_sentence_id, "statement": self.statement,
                "subsection": self.subsection, "similarity": self.similarity,
                "distance_to_tau": self.distance_to_tau,
                "closest_sentence": self.closest_sentence, "closest_course": self.closest_course}
