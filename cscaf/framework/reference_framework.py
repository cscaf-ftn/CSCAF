"""A reference framework of role profiles, each with skill and knowledge statements (Section 3.1 of the paper)."""
from __future__ import annotations

import abc


class ReferenceFramework(abc.ABC):
    """Role profiles read from the framework's own release, checked before anything is stored.

    A subclass names the roles and reads the profiles; the order and the checks are fixed here (Template Method).
    """

    SUBSECTIONS: tuple[tuple[str, str], ...] = (("skills", "key_skills"), ("knowledge", "key_knowledge"))

    @abc.abstractmethod
    def _read(self) -> list[dict]:
        """The profiles of the release, each a dict with a `title` and one list of statements per subsection."""

    @abc.abstractmethod
    def short_name(self, title: str) -> str:
        """The project's short name of a role (e.g. `PenTester`)."""

    @abc.abstractmethod
    def _check(self, profiles: list[dict]) -> None:
        """Raise when the release is not the one the study was run on."""

    def profiles(self) -> list[dict]:
        """The checked role profiles."""
        profiles = self._read()
        self._check(profiles)
        return profiles
