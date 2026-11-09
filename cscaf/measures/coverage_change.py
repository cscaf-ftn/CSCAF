"""The change of role coverage when a course is added (Section 4.2 of the paper)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CoverageChange:
    """What adding one text did to one programme, per role and per statement."""

    curriculum_key: str
    added: str
    tau: float
    sentences_added: int = 0
    before: dict[str, float] = field(default_factory=dict)
    after: dict[str, float] = field(default_factory=dict)
    statements_before: int = 0
    statements_after: int = 0
    crossed: list[int] = field(default_factory=list)

    @property
    def delta(self) -> dict[str, float]:
        """delta C(r) per role."""
        return {role: self.after[role] - self.before[role] for role in self.before}

    def delta_for(self, role: str) -> float:
        """delta C(r) for one role."""
        return self.after[role] - self.before[role]

    @property
    def roles_moved(self) -> dict[str, float]:
        """Only the roles that moved, largest first; a role may move by one statement."""
        moved = {role: value for role, value in self.delta.items() if value > 1e-9}
        return dict(sorted(moved.items(), key=lambda pair: -pair[1]))

    def as_dict(self) -> dict:
        return {"curriculum_key": self.curriculum_key, "added": self.added, "tau": self.tau,
                "sentences_added": self.sentences_added,
                "statements_before": self.statements_before, "statements_after": self.statements_after,
                "crossed": sorted(self.crossed), "before": self.before, "after": self.after,
                "delta": self.delta, "roles_moved": self.roles_moved}
