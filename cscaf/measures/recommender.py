"""The recommended statements of Section 4.2 of the paper: which statements a programme should state next.

For a programme and a target ECSF role, the rule returns up to two skill and up to two knowledge statements, those
with the highest similarity below tau: the competencies the programme comes closest to covering without covering
them. Each comes with the curriculum sentence of its best match, so a coordinator can see whether the competency is
already taught and only needs to be written down.

Advertisements take no part: the recommendation is a function of the curriculum-framework relation only, and the
target role is named by the institution. A subsection may hold fewer than two statements below tau, so a
recommendation carries four, three, two, one or no statements. A role with nothing below tau gets no recommendation.
"""
from __future__ import annotations

from cscaf.measures.recommendation import Recommendation
from cscaf.measures.recommended_statement import RecommendedStatement


class Recommender:
    """The recommendation rule, at the tau of a study."""

    SKILLS = "skills"
    KNOWLEDGE = "knowledge"
    PER_SUBSECTION = 2

    def __init__(self, study, per_subsection: int = PER_SUBSECTION):
        self.tau = study.tau
        self.per_subsection = per_subsection

    def recommend(self, items: dict, mapping, role: str, curriculum_key: str = "",
                  matches: dict | None = None) -> Recommendation:
        """The recommended statements for one programme and one target role.

        Args:
            items: the `items` of one curriculum, as `CurriculumCoverage.statements` returns them
            mapping: the `RoleMapping`
            role: the target role, e.g. `PenTester`
            curriculum_key: recorded on the result; the rule does not use it
            matches: optional {rf_sentence_id: {"sentence", "course"}}, the curriculum sentence of each best match

        Returns:
            Recommendation: up to `per_subsection` statements per subsection, skills first and by descending
            similarity within a subsection; `fully_covered` when the role has no statement below tau

        Raises:
            ValueError: the role is not in the mapping, which means a typo rather than an empty result
        """
        threshold = self.tau
        own: list[tuple[int, str, str]] = []
        role_name = ""
        for rf_id, roles in mapping.items():
            for entry in roles:
                if entry["role"] == role:
                    role_name = entry["role_name"]
                    own.append((rf_id, entry["subsection"], entry["statement"]))
        if not own:
            raise ValueError(f"role {role!r} is not in the item-role mapping")

        below: dict[str, list[RecommendedStatement]] = {self.SKILLS: [], self.KNOWLEDGE: []}
        for rf_id, subsection, statement in own:
            similarity = items.get(rf_id, {}).get("similarity")
            if similarity is None or similarity >= threshold:
                continue
            match = (matches or {}).get(rf_id) or {}
            below.setdefault(subsection, []).append(RecommendedStatement(
                rf_sentence_id=rf_id, statement=statement, subsection=subsection,
                similarity=float(similarity), distance_to_tau=float(threshold - similarity),
                closest_sentence=match.get("sentence"), closest_course=match.get("course")))

        chosen: list[RecommendedStatement] = []
        for name in (self.SKILLS, self.KNOWLEDGE):
            ordered = sorted(below.get(name, []), key=lambda s: (-s.similarity, s.rf_sentence_id))
            chosen += ordered[:self.per_subsection]

        return Recommendation(
            curriculum_key=curriculum_key, role=role, role_name=role_name, tau=threshold,
            statements=chosen, fully_covered=not chosen,
            statements_below_tau={name: len(below.get(name, [])) for name in (self.SKILLS, self.KNOWLEDGE)})

    @staticmethod
    def best_matches(storage, run_id: str, curriculum_key: str) -> dict:
        """{rf_sentence_id: {"sentence", "course", "similarity"}} for one programme: the sentence behind each best
        match, read from the database."""
        rows = storage.similarities.curriculum_best_match_sentences(run_id)
        if rows is None:
            raise Exception("Error reading the curriculum best matches")
        return {row[0]: {"sentence": row[3], "course": row[6], "similarity": float(row[4])}
                for row in rows if row[5] == curriculum_key}
