"""The English check of every text loaded into the database (Section 3.2 of the paper).

A line reads as another language when it holds more function words of that language than of English (at least
`MIN_HITS`); a line with a single such word and at most one English one is decided by langdetect. A line that is
not in English is reported as an error by the loaders and does not stop a load.
"""
from __future__ import annotations

import re


class LanguageCheck:
    """Which lines of a text are not in English."""

    MIN_HITS = 2
    LANGDETECT_MIN_PROBABILITY = 0.90
    LANGDETECT_MIN_WORDS = 4
    FUNCTION_WORDS = {
        "en": "the of and for with from that this which are be been have has will would should their they you your our we it its at by an or not as can".split(),
        "fr": "le la les des du de et un une pour avec dans sur est sont nous vous qui que au aux ces cette votre notre leur être chez vos nos maîtrise connaissance".split(),
        "de": "der das und ist mit für von zu den dem des ein eine einer wir sie ihr nicht auf im bei oder auch sind werden über unter sowie deine ihre unsere kenntnisse erfahrung".split(),
        "it": "il lo gli della delle dei di e per con che sono una un nel nella alla del le si come anche essere".split(),
        "es": "el los las del de y para con que por una un en es son como sus nuestro nuestra al se".split(),
        "nl": "de het een van en voor met zijn wij jij je ons onze bij op dat deze naar ook niet wordt zoals andere uit jouw hebt ben over als wat hoe heb kun kunt binnen tussen onder".split(),
        "pt": "o os as da do das dos de e para com que uma um em é são nossa nosso ao pelo pela".split(),
        "ro": "și în pentru cu de la din care este sunt un o al ale cel mai pe vă noi".split(),
        "pl": "i w z na do że się jest są dla oraz lub od przez jako nie".split(),
        "sv": "och att för med som är av på en ett vi du till har det inte".split(),
        "da": "og at for med som er af på en et vi du til har det ikke".split(),
        "fi": "ja on että ole tai kanssa sekä myös joka".split(),
        "cs": "a v na je se že s pro z do jako které".split(),
        "sk": "a v na je sa že s pre z do ako ktoré".split(),
        "hu": "és a az hogy egy nem van vagy is meg".split(),
        "el": "και το η ο του της των για με σε από".split(),
        "bg": "и в на за с от да се е са по като или които че към при това".split(),
    }
    _SHARED_WITH_ENGLISH = set(FUNCTION_WORDS["en"]) | {"a", "i", "in", "is", "to", "on", "die", "as", "be", "o", "e", "se"}

    @staticmethod
    def _vocabulary(function_words: dict[str, list[str]], shared: set[str]) -> dict[str, set[str]]:
        """The evidence words of each language: its function words without those shared with English."""
        return {language: set(words) if language == "en" else set(words) - shared
                for language, words in function_words.items()}

    _VOCABULARY = _vocabulary(FUNCTION_WORDS, _SHARED_WITH_ENGLISH)
    _WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

    @staticmethod
    def line_language(line: str) -> tuple[str, int] | None:
        """(language, function words found) when the line reads as a language other than English, else None."""
        words = {word.lower() for word in LanguageCheck._WORD.findall(line or "")}
        english = len(words & LanguageCheck._VOCABULARY["en"])
        best, hits = None, 0
        for language, vocabulary in LanguageCheck._VOCABULARY.items():
            if language == "en":
                continue
            found = len(words & vocabulary)
            if found > hits:
                best, hits = language, found
        if hits >= LanguageCheck.MIN_HITS and hits > english:
            return best, hits
        if hits == 1 and english <= 1 and len((line or "").split()) >= LanguageCheck.LANGDETECT_MIN_WORDS:
            detected, probability = LanguageCheck._langdetect(line)
            if detected == best and probability >= LanguageCheck.LANGDETECT_MIN_PROBABILITY:
                return best, hits
        return None

    @classmethod
    def non_english_lines(cls, text: str) -> list[tuple[int, str, str]]:
        """(line number from 1, language, line) for every line read as another language."""
        found = []
        for number, line in enumerate((text or "").split("\n"), start=1):
            language = cls.line_language(line)
            if language:
                found.append((number, language[0], line.strip()))
        return found

    @classmethod
    def is_english(cls, text: str) -> bool:
        """True when no line of the text reads as another language. An empty text is English."""
        return not cls.non_english_lines(text)

    @staticmethod
    def _langdetect(text: str) -> tuple[str | None, float]:
        """The most likely language by langdetect, with its probability, or (None, 0)."""
        try:
            from langdetect import DetectorFactory, detect_langs
            DetectorFactory.seed = 0
            best = detect_langs(text)[0]
            return best.lang, best.prob
        except Exception:
            return None, 0.0
