"""The recommendation for one curriculum and one target role (Section 4.2)."""
from __future__ import annotations

from dataclasses import dataclass, field

from cscaf.measures.recommended_statement import RecommendedStatement


@dataclass(frozen=True)
class Recommendation:
    """The recommendation for one programme and one target role."""

    curriculum_key: str
    role: str
    role_name: str
    tau: float
    statements: list[RecommendedStatement] = field(default_factory=list)
    fully_covered: bool = False
    statements_below_tau: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"curriculum_key": self.curriculum_key, "role": self.role, "role_name": self.role_name,
                "tau": self.tau, "fully_covered": self.fully_covered,
                "statements_below_tau": self.statements_below_tau,
                "statements": [s.as_dict() for s in self.statements]}
