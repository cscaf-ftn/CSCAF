"""What the preprocessing of one text changed (Section 3.3 of the paper)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PreprocessingReport:
    """How many changes each step made to one text."""
    unicode_characters: int = 0
    whitespace_lines: int = 0
    dehyphenations: int = 0
    inline_items_split: int = 0
    list_items: int = 0
    joined_lines: int = 0
    periods_added: int = 0
    closed_lines: list[int] = field(default_factory=list, repr=False)

    def as_dict(self) -> dict:
        """The counts of changes; `closed_lines` is a position list, not a count, and is left out."""
        return {key: value for key, value in self.__dict__.items() if key != "closed_lines"}

    def changed(self) -> bool:
        return any(value for key, value in self.as_dict().items() if key != "list_items")
