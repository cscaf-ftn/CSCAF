"""Known-groups validity of the measures (Section 4.1 of the paper, Table 3).

Groups whose answer is known from outside the measurement must be separated in the expected direction:

- advertisements whose title names a role must require the statements of that role more often than the rest of the
  corpus, and that role should be the strongest of the twelve for the group;
- curricula with a course named after a role area must cover that role better than curricula without one.

The keyword lists live in `config.yaml` (Supplementary Table S3), so neither they nor the expectation can be adjusted
to the result. Both comparisons are between sets, never between single advertisements.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np
from scipy.stats import mannwhitneyu

from cscaf.measures.curriculum_coverage import CurriculumCoverage
from cscaf.measures.role_mapping import RoleMapping


class KnownGroups:
    """The known-groups check at the tau of a study."""

    def __init__(self, study, storage):
        self.study = study
        self.storage = storage
        self.settings = study.config["known_groups"]

    @staticmethod
    def matches(text: str, needles: list[str]) -> bool:
        """Whether a lower-cased text contains any of the keywords of a group."""
        lowered = (text or "").lower()
        return any(needle in lowered for needle in needles)

    @staticmethod
    def _effect(selected: np.ndarray, rest: np.ndarray) -> tuple[float, float]:
        """One-sided Mann-Whitney p value and the rank-biserial effect size, for 'selected is larger'."""
        if len(selected) < 2 or len(rest) < 2:
            return float("nan"), float("nan")
        result = mannwhitneyu(selected, rest, alternative="greater")
        effect = 2 * result.statistic / (len(selected) * len(rest)) - 1
        return float(result.pvalue), float(effect)

    def advertisements(self, titles: dict) -> list[dict]:
        """Does a title that names a role predict demand for that role?

        Args:
            titles: {advertisement id: title}

        Returns:
            one entry per group: its size, the role's share of statements inside and outside the group, the place
            of that role among the twelve for the group, and the test
        """
        threshold = self.study.tau
        per_role = RoleMapping.read(self.storage).statements_per_role()

        loaded = self.storage.similarities.advertisement_item_scores(self.study.run_id, None, None, None)
        if loaded is None:
            raise Exception("Error reading the job advertisement item scores")
        _, rows = loaded
        covered = defaultdict(set)
        for advertisement_id, rf_id, score in rows:
            if score >= threshold:
                covered[advertisement_id].add(int(rf_id))

        def share(advertisement_ids, role):
            statements = per_role[role]
            return np.array([len(covered.get(a, set()) & statements) / len(statements)
                             for a in advertisement_ids], dtype=float)

        report = []
        for role, needles in self.settings["advertisement_titles"].items():
            inside = [a for a, title in titles.items() if self.matches(title, needles)]
            outside = [a for a in titles if a not in set(inside)]
            entry = {"role": role, "keywords": needles, "advertisements": len(inside)}
            if len(inside) < self.settings["minimum_group"]:
                entry["enough"] = False
                report.append(entry)
                continue
            mine, others = share(inside, role), share(outside, role)
            ranking = sorted(per_role, key=lambda other: -share(inside, other).mean())
            p_value, effect = self._effect(mine, others)
            entry.update({"enough": True, "inside": float(mine.mean()), "outside": float(others.mean()),
                          "ratio": float(mine.mean() / others.mean()) if others.mean() else float("inf"),
                          "rank_of_role": ranking.index(role) + 1, "strongest_role": ranking[0],
                          "p_value": p_value, "effect_size": effect})
            report.append(entry)
        return report

    def curricula(self, courses: dict) -> list[dict]:
        """Does a course named after a role area predict coverage of that role?

        Args:
            courses: {curriculum key: [course name, ...]}
        """
        mapping = RoleMapping.read(self.storage)
        coverage = CurriculumCoverage(self.study, self.storage).statements(None)
        per_curriculum = {key: CurriculumCoverage.roles(entry["items"], mapping) for key, entry in coverage.items()}

        report = []
        for role, needles in self.settings["course_names"].items():
            inside = [key for key in per_curriculum
                      if any(self.matches(name, needles) for name in courses.get(key, []))]
            outside = [key for key in per_curriculum if key not in set(inside)]
            entry = {"role": role, "keywords": needles, "with_course": len(inside),
                     "without_course": len(outside)}
            if not inside or not outside:
                entry["enough"] = False
                report.append(entry)
                continue
            mine = np.array([per_curriculum[key][role]["coverage"] for key in inside])
            others = np.array([per_curriculum[key][role]["coverage"] for key in outside])
            p_value, effect = self._effect(mine, others)
            entry.update({"enough": True, "inside": float(mine.mean()), "outside": float(others.mean()),
                          "ratio": float(mine.mean() / others.mean()) if others.mean() else float("inf"),
                          "p_value": p_value, "effect_size": effect})
            report.append(entry)
        return report

    @staticmethod
    def summary(advertisements: list[dict], curricula: list[dict], alpha: float = 0.05) -> dict:
        """Whether the check passes, counted over every group that was large enough.

        The pass condition was fixed before the check was run: on the advertisement side the named role must score
        higher inside the group than outside it in every group tested and be the strongest of the twelve in most of
        them; on the curriculum side the direction must hold in most groups and be significant in at least three.
        """
        ads = [entry for entry in advertisements if entry.get("enough")]
        programmes = [entry for entry in curricula if entry.get("enough")]
        higher = sum(1 for entry in ads if entry["inside"] > entry["outside"])
        first = sum(1 for entry in ads if entry["rank_of_role"] == 1)
        direction = sum(1 for entry in programmes if entry["inside"] > entry["outside"])
        significant = sum(1 for entry in programmes if entry["p_value"] < alpha)
        return {"advertisement_groups": len(ads), "advertisement_higher": higher,
                "advertisement_role_first": first, "curriculum_groups": len(programmes),
                "curriculum_direction": direction, "curriculum_significant": significant,
                "passes": higher == len(ads) and first > len(ads) / 2
                          and direction > len(programmes) / 2 and significant >= 3}
