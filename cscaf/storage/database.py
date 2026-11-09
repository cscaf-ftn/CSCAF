"""The SQLite database of the study and the base of its repositories.

The analysis opens the database read-only; only the loading notebooks of `data_load/` open it for writing.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


class Database:
    """One SQLite file, opened read-only unless writing is asked for."""

    def __init__(self, path: Path | str, read_only: bool = True):
        self.path = Path(path)
        self.read_only = read_only

    def connect(self) -> sqlite3.Connection:
        if self.read_only:
            return sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro", uri=True)
        return sqlite3.connect(self.path)

    def create(self, schema: Path | str) -> bool:
        """Create the database from the schema file unless it exists; True when it was created."""
        if self.path.exists():
            return False
        with sqlite3.connect(self.path) as connection:
            connection.executescript(Path(schema).read_text(encoding="utf-8"))
        return True

    def count_rows(self, table: str, run_id: str | None = None) -> int | None:
        """The rows of a table, or of one run when `run_id` is given.

        The table name cannot be a query parameter, so it is accepted only if a table or view of that exact name
        exists. Returns None if it does not exist; raises ValueError if `run_id` is given for a table without a
        run_id column.
        """
        with self.connect() as db:
            exists = db.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?",
                                (table,)).fetchone()
            if not exists:
                return None
            if run_id is None:
                return db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            columns = {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}
            if "run_id" not in columns:
                raise ValueError(f"table {table} has no run_id column")
            return db.execute(f'SELECT COUNT(*) FROM "{table}" WHERE run_id = ?', (run_id,)).fetchone()[0]
