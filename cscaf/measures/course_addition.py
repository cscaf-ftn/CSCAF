"""The course addition of Section 4.2 of the paper: the change of role coverage when a course is added.

The published description of an existing course is added to a programme and the programme is measured again with
the same instrument and threshold:

    delta C(r) = C'(r) - C(r)

Because coverage is a maximum over sentences, the extended programme's best match for a statement is the larger of
the two best matches, so the simulation needs no new embedding. delta C(r) is never negative, moves in steps of
1 / |S_r| and grows with the amount of text added, so it is read only against control courses, with the number of
sentences added beside it.

A course aimed at one role can raise another through the statements the two roles share. If roles r and q share k
statements, covering all of them raises q by at most k / |S_q|: the ceiling of the overlap. A rise above it, or in a
role that shares nothing, is the text covering that role on its own.
"""
from __future__ import annotations

from collections import Counter

from cscaf.measures.coverage_change import CoverageChange


class CourseAddition:
    """The course-addition simulation at the tau of a study."""

    def __init__(self, study):
        self.tau = study.tau

    @staticmethod
    def role_coverage(scores: dict, mapping, threshold: float) -> dict[str, float]:
        """C(r) of Equation (3) under the binary weighting, from {rf_sentence_id: best similarity}.

        A statement with no score is not covered: it counts in the denominator as a zero.
        """
        per_role: dict[str, list[int]] = {}
        for rf_id, roles in mapping.items():
            for entry in roles:
                per_role.setdefault(entry["role"], []).append(rf_id)
        return {role: sum(1 for rf_id in items if scores.get(rf_id, -1.0) >= threshold) / len(items)
                for role, items in per_role.items()}

    def change(self, base_scores: dict, added_scores: dict, mapping, curriculum_key: str = "", added: str = "",
               sentences_added: int = 0, target_statements: list[int] | None = None) -> CoverageChange:
        """Coverage before and after a text is added to a programme.

        Args:
            base_scores: {rf_sentence_id: best similarity} for the programme
            added_scores: {rf_sentence_id: best similarity} for the text being added
            mapping: the `RoleMapping`
            curriculum_key, added: recorded on the result
            sentences_added: how many sentences the added text contributed, reported with every delta
            target_statements: the statements to watch; `crossed` reports which of them the addition lifted
                above tau
        """
        threshold = self.tau
        union = {rf_id: max(base_scores.get(rf_id, -1.0), added_scores.get(rf_id, -1.0))
                 for rf_id in mapping}
        crossed = [rf_id for rf_id in (target_statements or [])
                   if base_scores.get(rf_id, -1.0) < threshold <= union.get(rf_id, -1.0)]
        return CoverageChange(
            curriculum_key=curriculum_key, added=added, tau=threshold,
            sentences_added=sentences_added,
            before=self.role_coverage(base_scores, mapping, threshold),
            after=self.role_coverage(union, mapping, threshold),
            statements_before=sum(1 for rf_id in mapping if base_scores.get(rf_id, -1.0) >= threshold),
            statements_after=sum(1 for rf_id in mapping if union.get(rf_id, -1.0) >= threshold),
            crossed=crossed)

    @staticmethod
    def overlap_ceilings(mapping, role: str) -> dict[str, float]:
        """The most each other role could gain through the statements it shares with `role`.

        Returns:
            {other role: k / |S_other|}, descending; a role absent from the result shares nothing with `role`
        """
        roles_of = {rf_id: [entry["role"] for entry in entries] for rf_id, entries in mapping.items()}
        sizes = Counter(name for names in roles_of.values() for name in names)
        if role not in sizes:
            raise ValueError(f"role {role!r} is not in the item-role mapping")
        shared: Counter = Counter()
        for rf_id, names in roles_of.items():
            if role in names:
                for other in names:
                    if other != role:
                        shared[other] += 1
        ceilings = {other: count / sizes[other] for other, count in shared.items()}
        return dict(sorted(ceilings.items(), key=lambda pair: -pair[1]))

    @classmethod
    def within_ceiling(cls, change: CoverageChange, mapping, role: str) -> dict[str, dict]:
        """Every other role that moved, with its ceiling and whether the overlap explains the movement.

        Returns:
            {role: {"delta", "ceiling", "within"}} for the roles that moved, largest delta first
        """
        ceilings = cls.overlap_ceilings(mapping, role)
        return {moved: {"delta": value, "ceiling": ceilings.get(moved, 0.0),
                        "within": value <= ceilings.get(moved, 0.0) + 1e-9}
                for moved, value in change.roles_moved.items() if moved != role}
