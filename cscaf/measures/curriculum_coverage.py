"""The curriculum side: statement coverage C_P(s) and role coverage C_P(r), Equations (2) and (3) of the paper.

C_P(s) is the weight of the best match of statement s over all sentences of all courses of curriculum P: is the
statement taught anywhere in the programme. C_P(r) is the mean of C_P(s) over the statements of role r. The unit is
one curriculum, whose text is fixed, so adding a curriculum cannot change the coverage of another, and coverage is
never pooled over curricula.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np

from cscaf.measures.bands import Bands


class CurriculumCoverage:
    """C_P(s) and C_P(r) for the curricula of a study, from the stored best matches."""

    def __init__(self, study, storage, bands_key: str = Bands.BINARY):
        self.study = study
        self.storage = storage
        self.bands = Bands.of(study, bands_key)

    def statements(self, curriculum_keys: list[str] | None = None) -> dict:
        """C_P(s), Equation (2), per curriculum.

        Returns:
            dict: {curriculum_key: {"country": str, "bands": key, "items": {rf_sentence_id:
            {"similarity": float, "coverage": float, "above_tau": bool}}}}
        """
        rows = self.storage.similarities.curriculum_item_scores(self.study.run_id, curriculum_keys)
        if rows is None:
            raise Exception("Error reading the curriculum item scores")
        if not rows:
            raise ValueError("no curriculum item scores for this run; compute the similarities first")
        threshold = self.bands.tau
        weights = self.bands.weights(np.array([row[3] for row in rows], dtype=float))
        coverage = {}
        for (key, country, rf_id, similarity), weight in zip(rows, weights):
            entry = coverage.setdefault(key, {"country": country, "bands": self.bands.key, "items": {}})
            entry["items"][rf_id] = {"similarity": float(similarity), "coverage": float(weight),
                                     "above_tau": bool(similarity >= threshold)}
        return coverage

    @staticmethod
    def roles(items: dict, mapping) -> dict:
        """C_P(r), Equation (3), for one curriculum, with the share above tau and the skills/knowledge split.

        Args:
            items: the `items` of one curriculum, as `statements` returns them
            mapping: the `RoleMapping`

        Returns:
            dict: {role: {"role_name", "coverage", "binary_share", "items", "covered_items", "subsections"}}
        """
        missing = {"coverage": 0.0, "above_tau": False, "similarity": None}
        per_role = defaultdict(lambda: defaultdict(list))
        names = {}
        for rf_id, roles in mapping.items():
            entry = items.get(rf_id, missing)
            for role in roles:
                names[role["role"]] = role["role_name"]
                per_role[role["role"]]["all"].append((rf_id, entry))
                per_role[role["role"]][role["subsection"]].append((rf_id, entry))

        def summarise(pairs):
            weights = [entry["coverage"] for _, entry in pairs]
            return {"coverage": float(np.mean(weights)), "items": len(pairs),
                    "binary_share": float(np.mean([entry["above_tau"] for _, entry in pairs])),
                    "covered_items": sorted(rf_id for rf_id, entry in pairs if entry["above_tau"])}

        result = {}
        for role, groups in per_role.items():
            result[role] = {"role_name": names[role], **summarise(groups["all"]),
                            "subsections": {name: summarise(pairs) for name, pairs in groups.items()
                                            if name != "all"}}
        return result
