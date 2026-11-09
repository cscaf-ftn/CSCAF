"""Deterministic preprocessing of a text before sentence segmentation (Section 3.3 of the paper).

Course descriptions copied from documents carry layout artefacts that a segmenter turns into wrong
units: lines wrapped inside a sentence, words hyphenated at the end of a line, list items written on
one line, and compatibility characters. The preprocessing removes these artefacts and nothing else.
It uses fixed rules, no model, and it never rewrites, paraphrases or reorders the content. The source
text is stored unchanged; the preprocessed text is derived from it on every run.

The steps run in a fixed order, and the order matters:

1. Unicode normalization, NFKC (Unicode Standard Annex #15). No conversion to ASCII.
2. Whitespace: line endings to LF, runs of spaces and tabs to one space, trailing spaces removed,
   three or more line breaks to one empty line.
3. De-hyphenation at the end of a line: "informa-" + "tion" becomes "information".
4. Structural segmentation: a line that starts with a list marker is a list item and always starts a
   new unit; items written on one line ("a • b • c") are put on lines of their own.
5. Joining wrapped lines: a line that continues the sentence of the previous line is joined to it.
   A list item is never joined to the line before it.
6. A list item without end punctuation receives a period, so that its end is explicit in the text.

Steps 4 and 5 must run in this order, because joining has to know where an item starts, and step 6
must come after step 5, or a period would land inside a sentence that was wrapped.

After these steps a line break marks the end of a unit by construction, which is what the segmenter's
`split_on_input_newlines: true` assumes.

The settings are read from `config.yaml` `segmentation.preprocessing`. `preprocess` returns the text
and a report with the number of changes each step made, so that the effect can be reported per
document.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from cscaf.text.preprocessing_report import PreprocessingReport


@dataclass
class _Line:
    text: str
    is_item: bool = False
    blank: bool = False


@dataclass
class TextPreprocessor:
    """The preprocessing rules, built once from `config.yaml` `segmentation.preprocessing`."""
    list_markers: tuple[str, ...]
    inline_markers: tuple[str, ...]
    end_punctuation: str
    continuation_words: frozenset[str]
    item_split_after: str = ".!?;"
    lead_in_endings: tuple[str, ...] = ()
    lead_in_max_words: int = 12
    _item_split: re.Pattern = field(init=False, repr=False)
    _start: re.Pattern = field(init=False, repr=False)
    _marker_only: re.Pattern = field(init=False, repr=False)
    _inline: re.Pattern = field(init=False, repr=False)
    _end: re.Pattern = field(init=False, repr=False)

    def __post_init__(self):
        markers = "|".join(re.escape(m) for m in self.list_markers)
        self._start = re.compile(rf"^(?:{markers}|\d{{1,2}}[.)]|[a-z][.)])\s+")
        self._marker_only = re.compile(rf"^({markers})\s+")
        inline = "".join(re.escape(m) for m in self.inline_markers)
        self._inline = re.compile(rf"\s+[{inline}]\s+")
        self._end = re.compile(rf"[{re.escape(self.end_punctuation)}]['\"’”)\]]*$")
        self._item_split = re.compile(rf"[{re.escape(self.item_split_after)}]['\"’”)\]]*$")

    @classmethod
    def from_config(cls, config: dict) -> "TextPreprocessor":
        settings = config["segmentation"]["preprocessing"]
        if not all(isinstance(w, str) for w in settings["continuation_words"]):
            raise ValueError("continuation_words must be quoted strings in config.yaml (YAML reads on/off/yes/no as booleans)")
        return cls(list_markers=tuple(settings["list_markers"]),
                   inline_markers=tuple(settings["inline_markers"]),
                   end_punctuation=settings["end_punctuation"],
                   continuation_words=frozenset(w.lower() for w in settings["continuation_words"]),
                   item_split_after=settings.get("item_split_after", ".!?;"),
                   lead_in_endings=tuple(p.lower() for p in settings.get("lead_in_endings", ())),
                   lead_in_max_words=int(settings.get("lead_in_max_words", 12)))


    @staticmethod
    def normalize_unicode(text: str, report: PreprocessingReport) -> str:
        """Step 1: NFKC. Counts the characters that change."""
        normalized = unicodedata.normalize("NFKC", text)
        if normalized != text:
            report.unicode_characters = sum(1 for c in text if unicodedata.normalize("NFKC", c) != c)
        return normalized

    @staticmethod
    def normalize_whitespace(text: str, report: PreprocessingReport) -> str:
        """Step 2: LF line endings, one space for runs of spaces and tabs, no trailing spaces, at most one
        empty line in a row."""
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        cleaned = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
        report.whitespace_lines += sum(1 for a, b in zip(lines, cleaned) if a != b)
        text, collapsed = re.subn(r"\n{3,}", "\n\n", "\n".join(cleaned))
        report.whitespace_lines += collapsed
        return text

    @staticmethod
    def dehyphenate(text: str, report: PreprocessingReport) -> str:
        """Step 3: a word broken at the end of a line ("informa-" / "tion") is put back together. Only
        when the line ends with a letter and a hyphen and the next line starts with a lower-case letter."""
        pattern = re.compile(r"([^\W\d_]{2,})-\n([a-z])")
        report.dehyphenations += len(pattern.findall(text))
        return pattern.sub(r"\1\2", text)

    def _is_item(self, line: str) -> bool:
        return bool(self._start.match(line))

    def _normalize_marker(self, line: str) -> str:
        """A list marker at the start of a line is written as the first inline marker ("•"), so that the
        cleanup after segmentation, which strips only its own markers, removes every kind. Without this
        "o Identification" (stpolten2026) and "◦ Analysis" kept their marker as part of the unit.
        Enumerators ("1.", "a)") are left as they are; the cleanup strips them separately."""
        match = self._marker_only.match(line)
        if match and match.group(1) != self.inline_markers[0]:
            return f"{self.inline_markers[0]} {line[match.end():]}"
        return line

    def split_inline_items(self, text: str, report: PreprocessingReport) -> list[_Line]:
        """Step 4: lines, each marked as list item or not; items written on one line are split. The text
        before the first inline marker, if any, stays a line of its own ("Cybercrime includes:")."""
        out = []
        for raw in text.split("\n"):
            if not raw:
                out.append(_Line("", blank=True))
                continue
            raw = self._normalize_marker(raw)
            parts = self._inline.split(raw)
            if len(parts) > 1:
                report.inline_items_split += len(parts) - 1
                first, items = parts[0], parts[1:]
                if self._is_item(first):
                    out.append(_Line(first, is_item=True))
                else:
                    out.append(_Line(first))
                out += [_Line(f"{self.inline_markers[0]} {item}", is_item=True) for item in items]
            else:
                out.append(_Line(raw, is_item=self._is_item(raw)))
        report.list_items = sum(1 for line in out if line.is_item)
        return out

    def _continues(self, previous: str, line: str) -> bool:
        """Whether `line` continues the sentence that `previous` leaves open."""
        if self._end.search(previous):
            return False
        last_word = previous.split()[-1].lower() if previous.split() else ""
        open_end = previous.endswith((",", "-", "–", "(")) or last_word in self.continuation_words
        return line[:1].islower() or open_end

    def join_wrapped(self, lines: list[_Line], report: PreprocessingReport) -> list[_Line]:
        """Step 5: a line is joined to the line before it when it continues that line's sentence. Never
        across an empty line, and never when the line starts a list item."""
        out: list[_Line] = []
        for line in lines:
            previous = out[-1] if out else None
            if (previous is not None and not line.blank and not previous.blank and not line.is_item
                    and self._continues(previous.text, line.text)):
                previous.text = f"{previous.text} {line.text}"
                report.joined_lines += 1
                continue
            out.append(_Line(line.text, line.is_item, line.blank))
        return out

    def close_items(self, lines: list[_Line], report: PreprocessingReport) -> list[_Line]:
        """Step 6: a list item without end punctuation receives a period. The positions of these items
        are recorded in `report.closed_lines`, so that the period can be removed after segmentation: it
        marks a boundary for the segmenter and is not part of the text the embedding model sees: a period alone moved the similarity by up to 0.06."""
        for index, line in enumerate(lines):
            if line.is_item and not self._end.search(line.text):
                line.text += "."
                report.periods_added += 1
                report.closed_lines.append(index)
        return lines


    def merge_within_items(self, text: str, units: list[str], closed_lines=()) -> tuple[list[str], int]:
        """A list item is one unit unless it holds several sentences.

        `text` is the preprocessed text and `units` what SaT made of it with line breaks forced, so no
        unit crosses a line. The units of each line are found again by their characters; inside a line
        that is a list item, a cut that does not follow sentence punctuation (`item_split_after`) is
        undone. Lines that are not list items are left as SaT cut them.

        `closed_lines` are the positions of the items that received a period in step 6
        (`PreprocessingReport.closed_lines`). That period is removed again from the last unit of the item,
        so the unit reads as in the source; a period the source itself had is kept.

        Returns the units and the number of cuts undone. If the units cannot be matched to the lines,
        they are returned unchanged (with the added periods still in place).
        """
        def squash(value: str) -> str:
            return re.sub(r"\s+", "", value)

        closed = set(closed_lines)
        merged, undone, position = [], 0, 0
        for index, line in enumerate(text.split("\n")):
            target, collected, have = squash(line), [], ""
            if not target:
                continue
            while position < len(units) and have != target:
                collected.append(units[position])
                have += squash(units[position])
                position += 1
                if not target.startswith(have):
                    return units, 0
            if not self._is_item(line):
                merged += collected
                continue
            pieces, current = [], ""
            for unit in collected:
                piece = unit.strip()
                if current and not self._item_split.search(current):
                    current = f"{current} {piece}"
                    undone += 1
                else:
                    if current:
                        pieces.append(current)
                    current = piece
            if current:
                pieces.append(current)
            if index in closed and pieces and pieces[-1].endswith("."):
                pieces[-1] = pieces[-1][:-1].rstrip()
            merged += [p for p in pieces if p]
        merged += units[position:]
        return merged, undone

    def is_lead_in(self, unit: str) -> bool:
        """Whether a unit is a lead-in to a list written without a colon ("…shall be able to"). Such a
        unit carries no content; the segmenter drops it, as the cleanup drops a unit ending with ":"."""
        tail = unit.strip().rstrip(",").strip().lower()
        if len(tail.split()) > self.lead_in_max_words:
            return False
        return any(tail == phrase or tail.endswith(" " + phrase) for phrase in self.lead_in_endings)


    def preprocess(self, text: str) -> tuple[str, PreprocessingReport]:
        """Steps 1-6 in order. Returns the preprocessed text and the report of changes."""
        report = PreprocessingReport()
        if not text:
            return text or "", report
        text = self.normalize_unicode(text, report)
        text = self.normalize_whitespace(text, report)
        text = self.dehyphenate(text, report)
        lines = self.split_inline_items(text, report)
        lines = self.join_wrapped(lines, report)
        while lines and lines[0].blank:
            lines.pop(0)
        while lines and lines[-1].blank:
            lines.pop()
        lines = self.close_items(lines, report)
        return "\n".join(line.text for line in lines), report
