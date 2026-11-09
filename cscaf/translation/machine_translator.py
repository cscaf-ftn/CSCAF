"""The interface every translation service implements, and the record of what each run spent."""
from __future__ import annotations

import abc
import os
from pathlib import Path


class MachineTranslator(abc.ABC):
    """One translation service: how much it takes per request, what it costs, and how it is called.

    The services differ in their limits and in their error codes, and in nothing else that matters
    here. `translate` always takes a list of source paragraphs and returns their translations in the
    same order, so the caller can pair them with the rows it sent.
    """

    name: str = "machine translation"
    max_texts: int = 50
    max_characters: int = 30_000
    monthly_characters: int | None = None
    characters_per_minute: int | None = None

    @abc.abstractmethod
    def translate(self, texts: list[str]) -> list[str]:
        """Translate one batch into English, in order."""

    def usage(self) -> dict | None:
        """Characters used and the limit, when the service reports it; otherwise None."""
        return None

    def check(self) -> str:
        """Translate one word, to prove the credentials work before a long run is started."""
        return self.translate(["Test"])[0]

    @staticmethod
    def read_credential(environment_variable: str, *paths: Path, required: bool = True) -> str | None:
        """A credential from the environment, or from the first file that exists next to the data.

        Several file names are accepted because the files are written by hand; the credentials live
        outside the repository and are never committed. With `required=False` a missing credential is not
        an error, which is how an optional setting such as the Azure region is read.
        """
        value = os.environ.get(environment_variable)
        if value:
            return value.strip()
        for path in paths:
            if path.is_file():
                return path.read_text(encoding="utf-8").strip()
        if not required:
            return None
        names = " or ".join(str(path) for path in paths)
        raise SystemExit(f"No credential: set {environment_variable} or put it in {names}")
