"""The job advertisements of the snapshot and their sentences."""

import json

import numpy as np

from cscaf.storage.repository import Repository


class AdvertisementRepository(Repository):
    """The job advertisements of the snapshot and their sentences."""

    def snapshot_id(self, source_sha256: str) -> int | None:
        try:
            with self._connect() as db:
                row = db.execute('SELECT id FROM job_advertisement_snapshot WHERE source_sha256 = ?',
                                 (source_sha256,)).fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Error reading job_advertisement_snapshot: {str(e)}")
            return None

    def save_snapshot(self, snapshot: dict, ads: list[tuple]) -> int | None:
        """
        Inserts one snapshot and its ads in one transaction: either all of them are stored or none.

        Args:
            snapshot: the job_advertisement_snapshot columns except id
            ads: (job_key, country_id, country, date_posted, date_posted_unix, location, company, title,
                title_before_translation, description, description_before_translation, content_hash) per ad

        Returns:
            int | None: the snapshot id, or None on failure
        """
        columns = ("created_at", "source_file", "source_sha256", "source_collection", "n_in_file", "n_not_eu",
                   "n_duplicates_removed", "n_loaded", "dedup_rule", "notes")
        try:
            with self._connect() as db:
                cursor = db.execute(f"INSERT INTO job_advertisement_snapshot ({', '.join(columns)}) "
                                    f"VALUES ({', '.join('?' * len(columns))})", tuple(snapshot[c] for c in columns))
                snapshot_id = cursor.lastrowid
                db.executemany(
                    'INSERT INTO job_advertisement (snapshot_id, job_key, country_id, country, date_posted, '
                    'date_posted_unix, location, company, title, title_before_translation, description, '
                    'description_before_translation, content_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    [(snapshot_id, *ad) for ad in ads])
                db.commit()
                return snapshot_id
        except Exception as e:
            print(f"Error saving job advertisement snapshot: {str(e)}")
            return None

    def texts(self) -> list[tuple[int, str, str, str]] | None:
        try:
            with self._connect() as db:
                return db.execute('SELECT id, job_key, title, description FROM job_advertisement ORDER BY id').fetchall()
        except Exception as e:
            print(f"Error reading job advertisements: {str(e)}")
            return None

    def to_segment(self, run_id: str) -> list[tuple[int, str, str, str]] | None:
        try:
            with self._connect() as db:
                return db.execute('''
                    SELECT ja.id, ja.job_key, ja.title, ja.description
                    FROM job_advertisement ja
                    WHERE NOT EXISTS (SELECT 1 FROM job_advertisement_sentence s
                                      WHERE s.run_id = ? AND s.job_advertisement_id = ja.id)
                    ORDER BY ja.id
                ''', (run_id,)).fetchall()
        except Exception as e:
            print(f"Error reading job advertisements to segment: {str(e)}")
            return None

    def save_sentences(self, rows: list[tuple], run_id: str) -> int | None:
        """
        Inserts the sentences of a batch of ads, with their embeddings, in one transaction.

        Args:
            rows: (ord, job_advertisement_id, job_key, part, sentence, embedding, embedding_dim,
                embedding_dtype, embedding_model) per sentence; each embedding is stored as a raw buffer
                of its dtype and its length is checked against embedding_dim, as in save_rf_sentence
            run_id: the run (configuration) that produced the sentences and vectors; see `ensure_run`

        Returns:
            int | None: the number of sentences stored, or None on failure
        """
        try:
            prepared = []
            for order, ad_id, job_key, part, sentence, embedding, dim, dtype, model in rows:
                values = embedding.cpu().numpy() if hasattr(embedding, "cpu") else np.asarray(embedding)
                vector = values.astype(np.dtype(dtype)).reshape(-1)
                if vector.size != dim:
                    raise ValueError(f"embedding of '{sentence[:40]}' has {vector.size} values, expected {dim}")
                prepared.append((run_id, order, ad_id, job_key, part, sentence, vector.tobytes(), dim, dtype, model))
            with self._connect() as db:
                db.executemany(
                    'INSERT INTO job_advertisement_sentence (run_id, ord, job_advertisement_id, job_key, part, '
                    'sentence, sentence_embedding, embedding_dim, embedding_dtype, embedding_model) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', prepared)
                db.commit()
            return len(prepared)
        except Exception as e:
            print(f"Error saving job advertisement sentences: {str(e)}")
            return None

    def ids_without_similarity(self, run_id: str) -> list[int] | None:
        try:
            with self._connect() as db:
                return [row[0] for row in db.execute('''
                    SELECT DISTINCT s.job_advertisement_id
                    FROM job_advertisement_sentence s
                    WHERE s.run_id = ?
                      AND NOT EXISTS (SELECT 1 FROM job_advertisement_rf_similarity_all a
                                      WHERE a.job_advertisement_sentence_id = s.id)
                    ORDER BY s.job_advertisement_id
                ''', (run_id,))]
        except Exception as e:
            print(f"Error reading job advertisements without similarity: {str(e)}")
            return None

    def sentence_embeddings(self, run_id: str, job_advertisement_ids: list[int]) \
            -> tuple[list[tuple[int, int]], np.ndarray, str] | None:
        try:
            with self._connect() as db:
                rows = db.execute('''
                    SELECT id, job_advertisement_id, sentence_embedding, embedding_dim, embedding_dtype,
                           embedding_model
                    FROM job_advertisement_sentence
                    WHERE run_id = ? AND job_advertisement_id IN (SELECT value FROM json_each(?))
                    ORDER BY id
                ''', (run_id, json.dumps(list(job_advertisement_ids)))).fetchall()
            if not rows:
                return [], np.zeros((0, 0)), ""
            matrix, model = self._decode_embeddings([row[2:] for row in rows])
            return [row[:2] for row in rows], matrix, model
        except Exception as e:
            print(f"Error reading job advertisement sentence embeddings: {str(e)}")
            return None

    def count(self) -> int:
        return self._one("SELECT COUNT(*) FROM job_advertisement")[0]

    def count_companies(self) -> int:
        return self._one("SELECT COUNT(DISTINCT company) FROM job_advertisement")[0]

    def count_countries(self) -> int:
        return self._one("SELECT COUNT(DISTINCT country_id) FROM job_advertisement")[0]

    def posting_period(self) -> tuple:
        """(first, last) posting date."""
        return self._one("SELECT MIN(date_posted), MAX(date_posted) FROM job_advertisement")

    def count_sentences(self, run_id: str) -> int:
        return self._one("SELECT COUNT(*) FROM job_advertisement_sentence WHERE run_id = ?", [run_id])[0]

    def count_without_sentences(self, run_id: str) -> int:
        """Advertisements left with no sentence of the run after the cleanup rules."""
        return self._one(
            "SELECT COUNT(*) FROM job_advertisement a WHERE NOT EXISTS (SELECT 1 FROM job_advertisement_sentence s "
            "WHERE s.job_advertisement_id = a.id AND s.run_id = ?)", [run_id])[0]

    def companies_and_descriptions(self) -> list[tuple]:
        return self._all("SELECT company, description FROM job_advertisement")

    def titles(self) -> list[tuple]:
        """(advertisement id, title, or an empty string)."""
        return self._all("SELECT id, COALESCE(title, '') FROM job_advertisement")

    def listing(self) -> list[tuple]:
        """(advertisement id, company, country, title), by id."""
        return self._all("SELECT id, TRIM(COALESCE(company, '')), country, COALESCE(title, '') FROM job_advertisement "
                         "ORDER BY id")

    def sentence(self, sentence_id: int | None) -> str | None:
        """The text of one advertisement sentence, or None when there is no such sentence."""
        row = self._one("SELECT sentence FROM job_advertisement_sentence WHERE id = ?", [sentence_id])
        return row[0] if row else None

    def count_with_sentence(self, sentence: str, advertisement_ids: list[int]) -> int:
        """How many of the advertisements contain exactly this sentence."""
        marks = ",".join("?" * len(advertisement_ids))
        return self._one(f"SELECT COUNT(DISTINCT job_advertisement_id) FROM job_advertisement_sentence WHERE sentence = ? "
                         f"AND job_advertisement_id IN ({marks})", [sentence, *advertisement_ids])[0]

    def locations(self, advertisement_ids: list[int]) -> list[str]:
        marks = ",".join("?" * len(advertisement_ids))
        return [location for (location,) in self._all(f"SELECT location FROM job_advertisement WHERE id IN ({marks})",
                                                      advertisement_ids)]

    def descriptions(self, advertisement_ids: list[int]) -> list[str]:
        marks = ",".join("?" * len(advertisement_ids))
        return [text for (text,) in self._all(f"SELECT description FROM job_advertisement WHERE id IN ({marks})",
                                              advertisement_ids)]
