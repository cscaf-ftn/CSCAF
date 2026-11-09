"""The report every load writes: what was stored, checked against the database, as a JSON file."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class LoadReport:
    """The base of the load reports. A subclass names its file and its content; this class writes it."""

    def _stem(self) -> str:
        raise NotImplementedError

    def _content(self, problems: list[str], finished_at: str) -> dict:
        raise NotImplementedError

    def write_report(self, folder: Path, problems: list[str]) -> Path:
        """Write the report under a time-stamped name in `folder`; an earlier report is never overwritten."""
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        finished = datetime.now(timezone.utc)
        stem = f"{self._stem()}_{finished.strftime('%Y%m%dT%H%M%SZ')}"
        path, suffix = folder / f"{stem}.json", 2
        while path.exists():
            path, suffix = folder / f"{stem}_{suffix}.json", suffix + 1
        content = self._content(problems, finished.isoformat(timespec="seconds"))
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
