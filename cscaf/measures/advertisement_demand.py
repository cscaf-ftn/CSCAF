"""The labour-market side: statement demand B_A(s), role demand B_A(r) and role lift L_A(r), Equations (4) to (6).

The unit of aggregation is the single advertisement. B_A(s) is the share of the advertisements of set A whose best
match for statement s reaches tau: the decision is taken for each advertisement separately and only then averaged.
N is the size of the whole set, including every advertisement whose best match is far below tau, so the measure
falls when unrelated advertisements are added. N is counted from the advertisements of the set, never from the rows
of the match table. B_A(s) is the observed share; no measure is corrected for the error of the matching rule.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np

from cscaf.measures.bands import Bands


class AdvertisementDemand:
    """B_A(s), B_A(r) and L_A(r) for sets of advertisements, from the stored best matches."""

    def __init__(self, study, storage, bands_key: str = Bands.BINARY):
        self.study = study
        self.storage = storage
        self.bands = Bands.of(study, bands_key)

    def _read(self, countries, date_from, date_to) -> tuple[int, list]:
        """The match rows of the set and N, counted from the advertisements themselves."""
        loaded = self.storage.similarities.advertisement_item_scores(self.study.run_id, countries, date_from, date_to)
        if loaded is None:
            raise Exception("Error reading the job advertisement item scores")
        n_ads, rows = loaded
        if n_ads == 0:
            raise ValueError("the set holds no advertisements, so there is no demand to compute")
        if not rows:
            raise ValueError(f"the set holds {n_ads} advertisements but the match table has no row for "
                             f"any of them; the similarities of this run are missing")
        return n_ads, rows

    def _items(self, rows: list, n_ads: int) -> dict:
        """B_A(s), the banded mean and the count of advertisements above tau, per statement."""
        rf_ids = np.array([row[1] for row in rows])
        scores = np.array([row[2] for row in rows], dtype=float)
        weights = self.bands.weights(scores)
        above = scores >= self.bands.tau
        items = {}
        for rf_id in np.unique(rf_ids):
            mine = rf_ids == rf_id
            items[int(rf_id)] = {"binary_share": float(above[mine].sum() / n_ads),
                                 "demand": float(weights[mine].sum() / n_ads),
                                 "ads_above_tau": int(above[mine].sum())}
        return items

    def _result(self, n_ads: int, items: dict, countries, date_from, date_to) -> dict:
        minimum = self.study.config["sets"]["minimum_job_advertisements"]
        return {"n_ads": int(n_ads), "recommended_minimum": int(minimum), "bands": self.bands.key,
                "below_recommended_minimum": bool(n_ads < minimum), "items": items,
                "filters": {"countries": countries, "date_from": date_from, "date_to": date_to}}

    def statements(self, countries: list[str] | None = None, date_from: str | None = None,
                   date_to: str | None = None) -> dict:
        """B_A(s), Equation (4), for the advertisements of the corpus selected by country and date.

        Returns:
            dict: {"n_ads": N, "items": {rf_sentence_id: {"binary_share", "demand", "ads_above_tau"}}, ...}
        """
        n_ads, rows = self._read(countries, date_from, date_to)
        return self._result(n_ads, self._items(rows, n_ads), countries, date_from, date_to)

    def of_rows(self, rows: list, n_ads: int) -> dict:
        """B_A(s), Equation (4), for any set of advertisements, from its best-match rows.

        For a set that is not a filter of the corpus, such as the advertisements of one employer, the caller passes
        the rows `(ad_id, rf_sentence_id, similarity)` of the set's advertisements and N, counted from the
        advertisements themselves (an advertisement without a row still counts).
        """
        if n_ads == 0:
            raise ValueError("the set holds no advertisements, so there is no demand to compute")
        result = self._result(n_ads, self._items(rows, n_ads) if rows else {}, None, None, None)
        result["filters"] = {"set": "rows"}
        return result

    @staticmethod
    def roles(demand: dict, mapping) -> dict:
        """B_A(r), Equation (5): the mean of B_A(s) over every statement the mapping gives the role.

        A statement that no advertisement of the set requires has no row in the match table; it counts as zero, so
        it stays in the denominator.
        """
        missing = {"demand": 0.0, "binary_share": 0.0, "ads_above_tau": 0}
        per_role = defaultdict(list)
        names = {}
        for rf_id, roles in mapping.items():
            entry = demand["items"].get(rf_id, missing)
            for role in roles:
                names[role["role"]] = role["role_name"]
                per_role[role["role"]].append(entry)
        roles = {}
        for role, entries in per_role.items():
            roles[role] = {"role_name": names[role], "items": len(entries),
                           "demand": float(np.mean([e["demand"] for e in entries])),
                           "binary_share": float(np.mean([e["binary_share"] for e in entries]))}
        total = sum(role["demand"] for role in roles.values())
        for role in roles.values():
            role["share"] = float(role["demand"] / total) if total else 0.0
        return roles

    @staticmethod
    def lift(set_demand: dict, rest_demand: dict, statements_per_role: dict) -> dict:
        """L_A(r) = B_A(r) / B_rest(r), Equation (6): the demand for a role in set A relative to the rest of the corpus.

        A lift above 1 means the set requires the role more often than the rest of the market. When the rest of the
        corpus never requires the role the lift is infinite, which a caller must not read as a preference by itself.

        Args:
            set_demand: {rf_sentence_id: B_A(s)}; a statement absent from it counts as 0
            rest_demand: {rf_sentence_id: B(s)} over the rest of the corpus
            statements_per_role: {role: iterable of rf_sentence_id}
        """
        lift = {}
        for role, statements in statements_per_role.items():
            statements = list(statements)
            inside = float(np.mean([set_demand.get(s, 0.0) for s in statements]))
            outside = float(np.mean([rest_demand.get(s, 0.0) for s in statements]))
            lift[role] = inside / outside if outside else float("inf")
        return lift

    def role_interval(self, mapping, countries: list[str] | None = None, date_from: str | None = None,
                      date_to: str | None = None, resamples: int = 2000, level: float = 0.95,
                      seed: int | None = None) -> dict:
        """B_A(r), Equation (5), with a percentile bootstrap interval that resamples the advertisements.

        The B_A(s) of a role are computed on the same advertisements, so they are not independent trials and a Wilson
        interval would understate the uncertainty. Advertisements that match no statement are part of the set and are
        resampled as columns of zeros.

        Returns:
            dict: {role: {"role_name", "items", "binary_share", "ci_low", "ci_high", "resamples", "level", "n_ads"}}
        """
        threshold = self.bands.tau
        n_ads, rows = self._read(countries, date_from, date_to)

        ad_ids = np.array([row[0] for row in rows])
        rf_ids = np.array([row[1] for row in rows])
        above = np.array([row[2] for row in rows], dtype=float) >= threshold

        statements = np.array(sorted(set(np.unique(rf_ids).tolist()) | set(mapping)))
        ads_present = np.unique(ad_ids)
        statement_at = {value: index for index, value in enumerate(statements)}
        ad_at = {value: index for index, value in enumerate(ads_present)}
        matrix = np.zeros((len(statements), n_ads), dtype=np.float32)
        for rf_id, ad_id, hit in zip(rf_ids, ad_ids, above):
            if hit:
                matrix[statement_at[rf_id], ad_at[ad_id]] = 1.0

        members = {}
        names = {}
        for index, rf_id in enumerate(statements):
            for role in mapping.get(int(rf_id), []):
                names[role["role"]] = role["role_name"]
                members.setdefault(role["role"], []).append(index)

        generator = np.random.default_rng(self.study.seed if seed is None else seed)
        draws = {role: np.empty(resamples) for role in members}
        for draw in range(resamples):
            counts = generator.multinomial(n_ads, np.full(n_ads, 1.0 / n_ads))
            shares = matrix @ counts / n_ads
            for role, indices in members.items():
                draws[role][draw] = shares[indices].mean()

        low, high = (1 - level) / 2 * 100, (1 + level) / 2 * 100
        point = matrix.mean(axis=1)
        result = {}
        for role, indices in members.items():
            result[role] = {"role_name": names[role], "items": len(indices),
                            "binary_share": float(point[indices].mean()),
                            "ci_low": float(np.percentile(draws[role], low)),
                            "ci_high": float(np.percentile(draws[role], high)),
                            "resamples": int(resamples), "level": float(level), "n_ads": int(n_ads)}
        return result
