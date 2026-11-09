"""Sentence segmentation with SaT (`wtpsplit`), driven by `config.yaml` `segmentation` (Section 3.3 of the paper).

The text is preprocessed, split by SaT, and cleaned by the rules of `config.yaml`: list markers and competence codes
are stripped, units ending with ":" and short lead-ins to a list are dropped, and so is document furniture. The model
is loaded once per (model, revision, device, precision) and reused.
"""
from __future__ import annotations

import re
import threading
from typing import Any, ClassVar, Iterable, Sequence

import emoji

from cscaf.text.text_preprocessor import TextPreprocessor


class SentenceSegmenter:
    """Splits text into sentences with the segmentation engine declared in `config.yaml`."""

    _ENUMERATOR = re.compile(r"^(?:(?:\d+(?:\.\d+)*[.)]|\d+(?:\.\d+)+|\(\d+\)|[A-Z]{1,3}\d+(?:\.\d+)*\.?|[a-z]\))(?=\s|$)"
                             r"|(?:\d+|[A-Z]{1,3}\d+)(?:\.\d+)*\.(?=[A-Z]))")
    _WORD = re.compile(r"[^\W\d_]{2,}")
    _LETTER = re.compile(r"[^\W\d_]")
    _DIGIT = re.compile(r"\d")
    _DECORATION = re.compile("[←-⇿☀-➿⬀-⯿‍︎️]")
    _heading_patterns: dict[tuple[str, ...], re.Pattern] = {}

    _models: ClassVar[dict[tuple[str, str, bool], Any]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    @classmethod
    def get_model(cls, config: dict):
        """Load (or reuse) the SaT model named in `config.yaml` `segmentation`."""
        settings = config["segmentation"]
        if settings["engine"] != "wtpsplit":
            raise ValueError(f"Unsupported segmentation engine: {settings['engine']}")
        key = (settings["model"], settings.get("model_revision"), settings.get("device", "cuda"),
               bool(settings.get("half_precision", False)))
        with cls._lock:
            if key not in cls._models:
                cls._models[key] = cls._load(*key)
        return cls._models[key]

    @classmethod
    def _load(cls, model: str, revision: str | None, device: str, half_precision: bool):
        """Load one SaT model at the revision pinned in `config.yaml`. Called under the lock, never directly."""
        import torch
        from wtpsplit import SaT

        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError(f"config.yaml requests device {device!r}, but no CUDA GPU is available")
        sat = SaT(model.split("/")[-1], from_pretrained_kwargs={"revision": revision} if revision else None)
        if half_precision:
            sat.half()
        sat.to(device)
        return sat

    @staticmethod
    def clean_units(units: Iterable[str], cleanup: dict) -> tuple[list[str], list[str]]:
        """Apply the cleanup rules. Returns (kept, dropped); `dropped` is for auditing.

        With `strip_enumerators`, a leading list number or competence code ("3.", "2)", "(1)",
        "7.2", "C4.2", "a)") is removed, alternating with the bullet markers until neither is left.
        With `drop_without_word`, a unit with no word of at least two letters ("3.", "C4.2", "N/A")
        is dropped.

        The remaining rules remove document furniture, which cannot express a competency and only
        creates false matches: emoji fragments, section headings ("Requirements", "HOW TO APPLY",
        "Learning objectives"), all-capital headings of two to five words, short questions
        ("What do we offer?") and units with too little content ("At"). See `furniture_reason`.
        """
        markers = tuple(cleanup.get("bullet_markers", ()))
        endings = tuple(cleanup.get("drop_if_ends_with", ()))
        minimum = cleanup.get("min_sentence_chars") or 0
        kept, dropped = [], []
        for unit in units:
            text = unit.strip()
            previous = None
            while text != previous:
                previous = text
                while markers and text[:1] in markers:
                    text = text[1:].strip()
                if cleanup.get("strip_enumerators", False):
                    text = SentenceSegmenter._ENUMERATOR.sub("", text, count=1).strip()
            if cleanup.get("drop_empty", True) and not text:
                if unit.strip().lstrip("".join(markers) + " "):
                    dropped.append(unit.strip())
                continue
            if cleanup.get("drop_without_word", False) and not SentenceSegmenter._WORD.search(text):
                dropped.append(unit.strip())
                continue
            if endings and text.endswith(endings):
                dropped.append(text)
                continue
            if minimum and len(text) < minimum:
                dropped.append(text)
                continue
            if SentenceSegmenter.furniture_reason(text, cleanup):
                dropped.append(unit.strip())
                continue
            if cleanup.get("strip_emoji", False) and SentenceSegmenter.has_decoration(text):
                text = SentenceSegmenter.strip_decoration(text)
                if not SentenceSegmenter._LETTER.search(text) or SentenceSegmenter.furniture_reason(text, cleanup):
                    dropped.append(unit.strip())
                    continue
            kept.append(text)
        return kept, dropped

    @classmethod
    def split(cls, text: str, config: dict, with_dropped: bool = False):
        """Split one text into sentences. Returns a list, or (kept, dropped) if asked."""
        kept, dropped = cls.split_many([text], config=config)[0]
        return (kept, dropped) if with_dropped else kept

    @classmethod
    def split_many(cls, texts: Sequence[str], config: dict) -> list[tuple[list[str], list[str]]]:
        """Split several texts in one pass. Returns (kept, dropped) per input text."""
        settings = config["segmentation"]
        cleanup = dict(settings.get("cleanup", {}))
        cleanup.setdefault("min_sentence_chars", settings.get("min_sentence_chars"))
        texts = list(texts)
        preprocessor, closed = None, [()] * len(texts)
        if settings.get("preprocessing", {}).get("enabled", False):
            preprocessor = TextPreprocessor.from_config(config)
            done = [preprocessor.preprocess(text) for text in texts]
            texts = [text for text, _ in done]
            closed = [report.closed_lines for _, report in done]
        raw = [list(units) for units in cls.get_model(config).split(
            texts, split_on_input_newlines=settings.get("split_on_input_newlines", True))]
        if preprocessor is not None and settings.get("split_on_input_newlines", True):
            raw = [preprocessor.merge_within_items(text, units, lines)[0]
                   for text, units, lines in zip(texts, raw, closed)]
        cleaned = [cls.clean_units(units, cleanup) for units in raw]
        if preprocessor is not None and preprocessor.lead_in_endings:
            cleaned = [([u for u in kept if not preprocessor.is_lead_in(u)],
                        dropped + [u for u in kept if preprocessor.is_lead_in(u)]) for kept, dropped in cleaned]
        return cleaned

    @classmethod
    def split_document(cls, parts: Sequence[str], config: dict) -> list[str]:
        """Split a document made of several parts and concatenate the sentences.

        Used for job ads, where the translated title and the translated description are
        segmented separately, so the title stays its own unit and is
        never glued to the first line of the description.
        """
        present = [part for part in parts if part and part.strip()]
        if not present:
            return []
        return [sentence for kept, _ in cls.split_many(present, config=config) for sentence in kept]

    @classmethod
    def clear_cache(cls) -> None:
        """Drop the loaded segmentation model (tests, GPU memory)."""
        with cls._lock:
            cls._models.clear()

    @staticmethod
    def _heading_pattern(patterns: Sequence[str]) -> re.Pattern:
        """The compiled "the whole unit is a section heading" pattern, cached per list from `config.yaml`."""
        key = tuple(patterns)
        if key not in SentenceSegmenter._heading_patterns:
            SentenceSegmenter._heading_patterns[key] = re.compile(r"^\W*(" + "|".join(patterns) + r")\W*$", re.IGNORECASE)
        return SentenceSegmenter._heading_patterns[key]

    @staticmethod
    def strip_decoration(text: str) -> str:
        """Remove emoji and decorative symbols, and close the gap they leave.

        The emoji themselves are removed with the `emoji` package, which follows the Unicode emoji data,
        rather than with a hand-written range: the data also covers the clock and keycap sequences
        ("1-keycap Requirements") and the trademark signs, which a range misses. `_DECORATION` then takes
        the symbols the emoji data does not list, because they are not emoji, but which are used in the
        same way in these documents.
        """
        return " ".join(SentenceSegmenter._DECORATION.sub("", emoji.replace_emoji(text, replace="")).split())

    @staticmethod
    def has_decoration(text: str) -> bool:
        """Whether the text holds any emoji or decorative symbol."""
        return emoji.emoji_count(text) > 0 or bool(SentenceSegmenter._DECORATION.search(text))

    @staticmethod
    def _carries_content(word: str) -> bool:
        """Whether a single word is enough on its own: a real word, or a domain acronym.

        "Risk" and "MPLS" are content by length. "IoT", "DNS" and "PKI" are shorter but are acronyms,
        which the corpus uses as topics in their own right; two or more capitals mark them. "At" and
        "En", the fragments left by a bad split or by an emoji bullet, are neither.
        """
        return len(word) >= 4 or sum(character.isupper() for character in word) >= 2

    @staticmethod
    def furniture_reason(text: str, cleanup: dict) -> str | None:
        """Why this unit is document furniture rather than content, or None if it is content.

        The rules were measured on the corpus of the study. Together they
        remove 2.8% of the curriculum units and 3.6% of the job-ad units, and only 0.3% of the units that
        are currently a best match above tau. They deliberately keep short domain phrases such as
        "Symmetric Cryptography", "Attack Libraries." or "ISO/IEC 27037:2012", which are content.
        """
        words = SentenceSegmenter._WORD.findall(text)
        if cleanup.get("drop_emoji_fragments", False) and len(words) <= 2 and SentenceSegmenter.has_decoration(text):
            return "emoji fragment"
        if cleanup.get("drop_section_headings", False) and cleanup.get("section_headings"):
            if SentenceSegmenter._heading_pattern(cleanup["section_headings"]).match(text):
                return "section heading"
        if cleanup.get("drop_all_caps_headings", False):
            if text.isupper() and 2 <= len(words) <= 5 and not SentenceSegmenter._DIGIT.search(text):
                return "all caps heading"
        if cleanup.get("drop_short_questions", False) and text.endswith("?") and len(words) <= 6:
            return "short question"
        if cleanup.get("require_content", False) and len(words) < 2 and not any(SentenceSegmenter._carries_content(w) for w in words):
            return "too little content"
        if cleanup.get("drop_single_words", False) and len(words) < 2 and len(text.split()) <= 1:
            if not (words and sum(character.isupper() for character in words[0]) >= 2):
                return "single word"
        return None
