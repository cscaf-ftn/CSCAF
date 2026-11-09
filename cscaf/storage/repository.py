"""The base of every repository of the storage."""
from __future__ import annotations

import sqlite3

import numpy as np

from cscaf.storage.database import Database


class Repository:
    """The base of every repository: the queries of one part of the schema over a shared `Database`."""

    def __init__(self, database: Database):
        self.database = database

    def _connect(self) -> sqlite3.Connection:
        return self.database.connect()

    def _all(self, query: str, arguments=()) -> list[tuple]:
        with self._connect() as db:
            return db.execute(query, arguments).fetchall()

    def _one(self, query: str, arguments=()) -> tuple:
        with self._connect() as db:
            return db.execute(query, arguments).fetchone()

    @staticmethod
    def _decode_embeddings(rows) -> tuple[np.ndarray, str]:
        """Stack (blob, dim, dtype, model) rows into one matrix; every row must come from the same model."""
        models = {row[3] for row in rows}
        if len(models) != 1:
            raise ValueError(f"expected vectors of one embedding model, found {sorted(map(str, models))}")
        vectors = []
        for blob, dim, dtype, _ in rows:
            vector = np.frombuffer(blob, dtype=np.dtype(dtype))
            if vector.size != dim:
                raise ValueError(f"stored vector has {vector.size} values, expected {dim}")
            vectors.append(vector)
        return np.vstack(vectors), models.pop()
