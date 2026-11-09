"""The demand-weighted gap G_P,A(r), Equation (7) of the paper.

For one curriculum P and one set of advertisements A, G is the share of the set's demand for the statements of role
r that falls on statements P does not cover:

    G(r) = sum_{s in r} B_A(s) * (1 - C_P(s)) / sum_{s in r} B_A(s)

It is 0 when P covers every statement the set requires and 1 when it covers none. Demand enters only as a weight.
"""
from __future__ import annotations


class DemandWeightedGap:
    """G_P,A(r) of Equation (7)."""

    @staticmethod
    def of_role(demand: dict, coverage: dict, statements) -> float | None:
        """G for one role.

        Args:
            demand: {rf_sentence_id: B_A(s)}; a statement absent from it has B_A(s) = 0
            coverage: {rf_sentence_id: C_P(s)}; a statement absent from it has C_P(s) = 0
            statements: the statements of the role

        Returns:
            G in [0, 1], or None when the set requires none of the role's statements (the gap is then undefined,
            not zero)
        """
        weight = sum(demand.get(s, 0.0) for s in statements)
        if weight == 0:
            return None
        uncovered = sum(demand.get(s, 0.0) * (1.0 - coverage.get(s, 0.0)) for s in statements)
        return uncovered / weight
