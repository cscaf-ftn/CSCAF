"""The characters sent to a machine translation service, per month."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path


class UsageLedger:
    """How many characters were sent to a service in each calendar month.

    Azure does not report usage through the translation API, so the only honest way to know what is
    left of a monthly allowance is to count what was sent. The ledger is written after every batch, so
    an interrupted run still leaves the count correct.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.months: dict[str, dict[str, int]] = {}
        if self.path.is_file():
            self.months = json.loads(self.path.read_text(encoding="utf-8"))

    def spent_this_month(self, service: str) -> int:
        return self.months.get(date.today().strftime("%Y-%m"), {}).get(service, 0)

    def add(self, service: str, characters: int) -> None:
        month = self.months.setdefault(date.today().strftime("%Y-%m"), {})
        month[service] = month.get(service, 0) + characters

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.months, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)
