"""Courses listed twice in a curriculum file, found and dropped before the curriculum is stored.

A course counts as a duplicate only when its name and its text are those of an earlier course of the same file: two
courses may share a name and teach different content in different semesters, and dropping one of those would delete
real material. A repeated name with a different text is kept and reported. The first copy is kept.
"""
from __future__ import annotations

import re
from collections import defaultdict


class DuplicateCourses:
    """Finds the courses listed twice in one curriculum document and drops the copies whose text repeats."""

    _WHITESPACE = re.compile(r"\s+")

    @classmethod
    def find(cls, courses: list[dict]) -> list[dict]:
        """Groups of courses of one curriculum that share a name, with whether their text agrees.

        Returns:
            one entry per repeated name, with the positions of the copies, whether every copy has the same text, and
            the length of each text
        """
        by_name = defaultdict(list)
        for position, course in enumerate(courses):
            by_name[cls._normalise(course.get("name", ""))].append(position)
        groups = []
        for name, positions in by_name.items():
            if len(positions) < 2:
                continue
            texts = [cls._normalise(courses[position].get("text", "")) for position in positions]
            groups.append({"name": courses[positions[0]].get("name", ""), "positions": positions,
                           "identical_text": len(set(texts)) == 1,
                           "lengths": [len(courses[position].get("text", "") or "") for position in positions]})
        return sorted(groups, key=lambda group: group["positions"][0])

    @classmethod
    def drop(cls, document: dict) -> tuple[dict, dict]:
        """A copy of the curriculum document without the repeated courses, and a report of what was dropped.

        Returns:
            (document without the duplicates, {"dropped": [...], "same_name_other_text": [...]})
        """
        courses = document.get("courses", [])
        dropped, kept_apart = [], []
        remove = set()
        for group in cls.find(courses):
            if group["identical_text"]:
                for position in group["positions"][1:]:
                    remove.add(position)
                    dropped.append({"name": group["name"], "position": position})
            else:
                kept_apart.append({"name": group["name"], "positions": group["positions"],
                                   "lengths": group["lengths"]})
        if not remove and not kept_apart:
            return document, {"dropped": [], "same_name_other_text": []}
        cleaned = {**document, "courses": [course for position, course in enumerate(courses)
                                           if position not in remove]}
        return cleaned, {"dropped": dropped, "same_name_other_text": kept_apart}

    @classmethod
    def _normalise(cls, text: str) -> str:
        """A name or a text reduced to what a comparison should see: case and spacing do not matter."""
        return cls._WHITESPACE.sub(" ", (text or "").strip()).casefold()
