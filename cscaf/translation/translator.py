"""Translation into English of the lines of a text that the English check flags (Section 3.2 of the paper).

The service is interchangeable (Strategy): `MachineTranslator` is the interface and `AzureTranslator` the
implementation used for the advertisements of the study. A line is sent with the language the English check found,
and every other line is kept as it is.
"""
from __future__ import annotations

from pathlib import Path

from cscaf.text.language_check import LanguageCheck
from cscaf.translation.azure_translator import AzureTranslator
from cscaf.translation.machine_translator import MachineTranslator


class Translator:
    """Translates the non-English lines of a text with one machine translation service."""

    def __init__(self, service: MachineTranslator):
        self.service = service

    @classmethod
    def azure(cls, credentials_folder: Path) -> "Translator":
        """The Azure AI Translator, with the credentials read from `credentials_folder`/keys or the environment."""
        return cls(AzureTranslator.from_files(Path(credentials_folder)))

    def translate(self, text: str, source: str | None = None) -> str:
        """The text with every non-English line translated into English, all other lines unchanged.

        `source` (ISO 639-1, e.g. "nl") names the language; without it each line goes with the language the
        English check found, because Azure's own detection takes some Dutch or French lines full of English
        terms for English and returns them unchanged.
        """
        lines = (text or "").split("\n")
        flagged = LanguageCheck.non_english_lines(text)
        by_language: dict[str, list[int]] = {}
        for number, language, _ in flagged:
            by_language.setdefault(source or language, []).append(number - 1)
        for language, indexes in by_language.items():
            translated = self.service.translate([lines[i] for i in indexes], source=language)
            for i, new in zip(indexes, translated):
                lines[i] = new
        return "\n".join(lines)
