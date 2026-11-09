"""The curricula, their courses (syllabi) and their sentences."""

from typing import List

import numpy as np

from cscaf.storage.curriculum_sentence import CurriculumSentence
from cscaf.storage.repository import Repository


class CurriculumRepository(Repository):
    """The curricula, their courses (syllabi) and their sentences."""

    def curriculum_id(self, curriculum_key: str) -> int | None:
        try:
            with self._connect() as db:
                row = db.execute('SELECT id FROM curriculum WHERE curriculum_key = ?', (curriculum_key,)).fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Error reading curriculum {curriculum_key}: {str(e)}")
            return None

    def save_curriculum(self, curriculum_key: str, university_name: str, faculty_name: str, programme_name: str,
                        friendly_name: str, short_name: str | None, year: int | None, country: str,
                        country_id: int, edition: str | None = None) -> int | None:
        """
        Inserts one curriculum (one study programme) and returns its id.

        `country` keeps the country name next to `country_id`, as the table defines it. `year` is the year the
        text was loaded (kept for the loaders and the curriculum editor); `edition` is the academic year of the
        published text, e.g. '2026/27'.
        """
        try:
            with self._connect() as db:
                cursor = db.cursor()
                cursor.execute(
                    'INSERT INTO curriculum (curriculum_key, university_name, faculty_name, programme_name, '
                    'friendly_name, short_name, year, country, country_id, edition) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (curriculum_key, university_name, faculty_name, programme_name, friendly_name, short_name,
                     year, country, country_id, edition)
                )
                db.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error saving curriculum {curriculum_key}: {str(e)}")
            return None

    def save_syllabus(self, curriculum_id: int, curriculum_key: str, name: str, ects_credits: float | None,
                      text: str) -> int | None:
        """Inserts one syllabus (one course) of a curriculum and returns its id."""
        try:
            with self._connect() as db:
                cursor = db.cursor()
                cursor.execute(
                    'INSERT INTO syllabus (curriculum_id, curriculum_key, name, ects_credits, text) '
                    'VALUES (?, ?, ?, ?, ?)',
                    (curriculum_id, curriculum_key, name, ects_credits, text)
                )
                db.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error saving syllabus {curriculum_key} / {name}: {str(e)}")
            return None

    def content_counts(self, curriculum_key: str, run_id: str) -> dict | None:
        """Counts what the database holds for one curriculum, to check a load against its log."""
        try:
            with self._connect() as db:
                syllabi = db.execute('SELECT COUNT(*) FROM syllabus WHERE curriculum_key = ?',
                                     (curriculum_key,)).fetchone()[0]
                sentences = db.execute('SELECT COUNT(*) FROM curriculum_sentence WHERE curriculum_key = ? '
                                       'AND run_id = ?', (curriculum_key, run_id)).fetchone()[0]
                return {"syllabi": syllabi, "sentences": sentences}
        except Exception as e:
            print(f"Error counting curriculum {curriculum_key}: {str(e)}")
            return None

    def curricula(self) -> list[tuple[int, str]] | None:
        try:
            with self._connect() as db:
                return db.execute('SELECT id, curriculum_key FROM curriculum ORDER BY id').fetchall()
        except Exception as e:
            print(f"Error reading curricula: {str(e)}")
            return None

    def sentence_embeddings(self, curriculum_key: str, run_id: str) \
            -> tuple[list[tuple[int, int, str]], np.ndarray, str] | None:
        try:
            with self._connect() as db:
                rows = db.execute('SELECT id, syllabus_id, syllabus_name, sentence_embedding, embedding_dim, '
                                  'embedding_dtype, embedding_model FROM curriculum_sentence '
                                  'WHERE curriculum_key = ? AND run_id = ? ORDER BY id',
                                  (curriculum_key, run_id)).fetchall()
            if not rows:
                return [], np.zeros((0, 0)), ""
            matrix, model = self._decode_embeddings([row[3:] for row in rows])
            return [row[:3] for row in rows], matrix, model
        except Exception as e:
            print(f"Error reading curriculum_sentence embeddings of {curriculum_key}: {str(e)}")
            return None

    def syllabi_with_text(self, curriculum_key: str | None = None) -> list[tuple] | None:
        """(syllabus id, curriculum id, curriculum key, name, text), ordered so the first copy is first."""
        try:
            with self._connect() as db:
                if curriculum_key is None:
                    return db.execute("""
                        SELECT id, curriculum_id, curriculum_key, name, text FROM syllabus
                        ORDER BY curriculum_key, id
                    """).fetchall()
                return db.execute("""
                    SELECT id, curriculum_id, curriculum_key, name, text FROM syllabus
                    WHERE curriculum_key = ? ORDER BY id
                """, (curriculum_key,)).fetchall()
        except Exception as e:
            print(f"Error reading the syllabi: {str(e)}")
            return None

    def syllabi_to_segment(self, run_id: str) -> list[tuple[int, int, str, str, str]] | None:
        """Syllabi that have no sentences for this run: (id, curriculum_id, curriculum_key, name, text)."""
        try:
            with self._connect() as db:
                return db.execute("""
                    SELECT s.id, s.curriculum_id, s.curriculum_key, s.name, s.text
                    FROM syllabus s
                    WHERE NOT EXISTS (SELECT 1 FROM curriculum_sentence c
                                      WHERE c.run_id = ? AND c.syllabus_id = s.id)
                    ORDER BY s.curriculum_key, s.id
                """, (run_id,)).fetchall()
        except Exception as e:
            print(f"Error reading syllabi to segment: {str(e)}")
            return None

    def save_sentences(self, sentences: List[CurriculumSentence], run_id: str) -> int | None:
        """
        Inserts the sentences of one syllabus, with their embeddings, in one transaction.

        Either every sentence of the list is stored or none is. Each embedding is stored as a raw
        buffer of the sentence's `embedding_dtype`, and its length is checked against
        `embedding_dim`, as in save_rf_sentence.

        Args:
            sentences: the sentences, each with `ord`, `syllabus_id`, `syllabus_name`,
                `curriculum_key`, `sentence` and the embedding fields; `id` is ignored
            run_id: the run (configuration) that produced the sentences and vectors; see `ensure_run`

        Returns:
            int | None: the number of sentences stored, or None on failure
        """
        try:
            rows = []
            for s in sentences:
                blob = None
                if s.sentence_embedding is not None:
                    values = s.sentence_embedding.cpu().numpy() if hasattr(s.sentence_embedding, "cpu") \
                        else np.asarray(s.sentence_embedding)
                    np_emb = values.astype(np.dtype(s.embedding_dtype)).reshape(-1)
                    if np_emb.size != s.embedding_dim:
                        raise ValueError(f"embedding of '{s}' has {np_emb.size} values, expected {s.embedding_dim}")
                    blob = np_emb.tobytes()
                rows.append((run_id, s.ord, s.syllabus_id, s.syllabus_name, s.curriculum_key, s.sentence, blob,
                             s.embedding_dim if blob is not None else None,
                             s.embedding_dtype if blob is not None else None,
                             s.embedding_model if blob is not None else None))
            with self._connect() as db:
                db.executemany(
                    'INSERT INTO curriculum_sentence (run_id, ord, syllabus_id, syllabus_name, curriculum_key, '
                    'sentence, sentence_embedding, embedding_dim, embedding_dtype, embedding_model) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', rows)
                db.commit()
            return len(rows)
        except Exception as e:
            print(f"Error saving curriculum sentences: {str(e)}")
            return None

    def keys(self) -> list[str]:
        """The keys of the stored curricula, sorted."""
        return [key for (key,) in self._all("SELECT curriculum_key FROM curriculum ORDER BY curriculum_key")]

    def editions(self) -> list[str]:
        return [edition for (edition,) in self._all("SELECT edition FROM curriculum")]

    def count(self) -> int:
        return self._one("SELECT COUNT(*) FROM curriculum")[0]

    def count_countries(self) -> int:
        return self._one("SELECT COUNT(DISTINCT country_id) FROM curriculum")[0]

    def count_courses(self) -> int:
        return self._one("SELECT COUNT(*) FROM syllabus")[0]

    def count_sentences(self, run_id: str) -> int:
        return self._one("SELECT COUNT(*) FROM curriculum_sentence WHERE run_id = ?", [run_id])[0]

    def programmes(self) -> list[tuple]:
        """(country, university, programme, edition, courses, key) per curriculum, by country (Table S1)."""
        return self._all("""
    SELECT c.country, c.university_name, c.programme_name, c.edition, COUNT(s.id), c.curriculum_key
    FROM curriculum c JOIN syllabus s ON s.curriculum_key = c.curriculum_key
    GROUP BY c.curriculum_key ORDER BY c.country
""")

    def course_names(self) -> list[tuple]:
        """(curriculum key, course name) for every course."""
        return self._all("SELECT curriculum_key, name FROM syllabus")

    def course_counts(self) -> dict:
        """{curriculum key: number of courses}."""
        return dict(self._all("SELECT curriculum_key, COUNT(*) FROM syllabus GROUP BY curriculum_key"))

    def course_count(self, curriculum_key: str) -> int:
        return self._one("SELECT COUNT(*) FROM syllabus WHERE curriculum_key = ?", [curriculum_key])[0]

    def sentence_counts(self, run_id: str) -> dict:
        """{curriculum key: number of sentences of the run}."""
        return dict(self._all("SELECT curriculum_key, COUNT(*) FROM curriculum_sentence WHERE run_id = ? "
                              "GROUP BY curriculum_key", [run_id]))

    def country_names(self) -> list[tuple]:
        """(curriculum key, country name)."""
        return self._all("SELECT c.curriculum_key, co.name FROM curriculum c JOIN country co ON co.id = c.country_id")
