"""The reference framework: roles, subsections, statements and their embeddings."""

import numpy as np

from cscaf.storage.repository import Repository


class FrameworkRepository(Repository):
    """The reference framework: roles, subsections, statements and their embeddings."""

    def save_section(self, short_name: str, full_name: str) -> int | None:
        """The id of this section, storing it first if it is not there yet.

        A section is the role profile itself and does not belong to a run: only the statements carry a
        `run_id`. So a reload under a new configuration finds the sections already in place and reuses
        them, exactly as a curriculum reload reuses its syllabi.
        """
        try:
            with self._connect() as db:
                cursor = db.cursor()
                cursor.execute(
                    'INSERT INTO rf_section (short_name, full_name) VALUES (?, ?) '
                    'ON CONFLICT (short_name) DO UPDATE SET full_name = excluded.full_name '
                    'RETURNING id',
                    (short_name, full_name)
                )
                row = cursor.fetchone()
                db.commit()
                return row[0] if row else None
        except Exception as e:
            print(f"Error saving rf_section: {str(e)}")
            return None

    def save_subsection(self, name: str, rf_section_id: int) -> int | None:
        """The id of this subsection ("skills", "knowledge") of a section, storing it if it is new.

        Like `save_rf_section`: structure is reused across runs, only the statements are made again.
        """
        try:
            with self._connect() as db:
                cursor = db.cursor()
                cursor.execute(
                    'INSERT INTO rf_subsection (name, rf_section_id) VALUES (?, ?) '
                    'ON CONFLICT (rf_section_id, name) DO UPDATE SET name = excluded.name '
                    'RETURNING id',
                    (name, rf_section_id)
                )
                row = cursor.fetchone()
                db.commit()
                return row[0] if row else None
        except Exception as e:
            print(f"Error saving rf_subsection: {str(e)}")
            return None

    def save_statement(self, sentence: str, sentence_embedding: np.ndarray, embedding_dim: int,
                         embedding_dtype: str, embedding_model: str, run_id: str) -> int | None:
        """
        Inserts one distinct statement, with its embedding and the fields needed to read it back.

        Args:
            sentence: the statement text (unique in rf_sentence)
            sentence_embedding: array (or tensor); stored as a raw buffer of `embedding_dtype`
            embedding_dim: vector length, e.g. 768
            embedding_dtype: numpy dtype of the stored buffer, e.g. "float32"
            embedding_model: the model that produced the vector
            run_id: the run (configuration) that produced the vector; see `ensure_run`
        """
        try:
            with self._connect() as db:
                cursor = db.cursor()
                existing = cursor.execute(
                    'SELECT id, run_id FROM rf_sentence WHERE sentence = ?', (sentence,)).fetchone()
                if existing is not None:
                    if existing[1] != run_id:
                        raise ValueError(f"the statement is already stored under run {existing[1]}; "
                                         f"delete that run before loading run {run_id}")
                    return existing[0]
                if sentence_embedding is not None:
                    values = sentence_embedding.cpu().numpy() if hasattr(sentence_embedding, "cpu") \
                        else np.asarray(sentence_embedding)
                    np_emb = values.astype(np.dtype(embedding_dtype)).reshape(-1)
                    if np_emb.size != embedding_dim:
                        raise ValueError(f"embedding has {np_emb.size} values, expected {embedding_dim}")
                    cursor.execute(
                        'INSERT INTO rf_sentence (run_id, sentence, sentence_embedding, embedding_dim, '
                        'embedding_dtype, embedding_model) VALUES (?, ?, ?, ?, ?, ?)',
                        (run_id, sentence, np_emb.tobytes(), embedding_dim, embedding_dtype, embedding_model)
                    )
                else:
                    cursor.execute('INSERT INTO rf_sentence (run_id, sentence) VALUES (?, ?)', (run_id, sentence))
                db.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error saving rf_sentence: {str(e)}")
            return None

    def save_subsection_statement(self, rf_subsection_id: int, rf_sentence_id: int, ord: int) -> int | None:
        try:
            with self._connect() as db:
                cursor = db.cursor()
                cursor.execute(
                    'INSERT INTO rf_subsection_sentence (rf_subsection_id, rf_sentence_id, ord) VALUES (?, ?, ?)',
                    (rf_subsection_id, rf_sentence_id, ord)
                )
                db.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error saving rf_subsection_sentence: {str(e)}")
            return None

    def item_roles(self) -> list[tuple] | None:
        try:
            with self._connect() as db:
                return db.execute('SELECT rf_sentence_id, section_short_name, section, sub_section, sentence '
                                  'FROM view_rf_sentences ORDER BY section_short_name, sub_section, ord').fetchall()
        except Exception as e:
            print(f"Error reading the item-role mapping: {str(e)}")
            return None

    def statement_embeddings(self, run_id: str) -> tuple[list[int], np.ndarray, str] | None:
        try:
            with self._connect() as db:
                rows = db.execute('SELECT id, sentence_embedding, embedding_dim, embedding_dtype, embedding_model '
                                  'FROM rf_sentence WHERE run_id = ? ORDER BY id', (run_id,)).fetchall()
            if not rows:
                return [], np.zeros((0, 0)), ""
            matrix, model = self._decode_embeddings([row[1:] for row in rows])
            return [row[0] for row in rows], matrix, model
        except Exception as e:
            print(f"Error reading rf_sentence embeddings: {str(e)}")
            return None

    def refresh_statement_view(self, **kwargs) -> int | None:
        """
        Refills the materialized table view_rf_sentences from the four rf_* tables.

        Call this after every change to rf_section, rf_subsection, rf_sentence or
        rf_subsection_sentence: the table is a copy, so until it is refreshed it shows the
        previous state. One row per role-statement pair, ordered by role, subsection and ord.

        Returns:
            int | None: the number of rows in the table afterwards, or None on failure
        """
        try:
            with self._connect() as db:
                db.execute("DELETE FROM view_rf_sentences")
                db.execute("""
                    INSERT INTO view_rf_sentences (id, ord, section, sub_section, sentence,
                                                   sentence_embedding, embedding_dim,
                                                   embedding_dtype, embedding_model,
                                                   rf_sentence_id, section_short_name)
                    SELECT rfss.id,
                           rfss.ord,
                           s.full_name   AS section,
                           r.name        AS sub_section,
                           rs.sentence,
                           rs.sentence_embedding,
                           rs.embedding_dim,
                           rs.embedding_dtype,
                           rs.embedding_model,
                           rs.id         AS rf_sentence_id,
                           s.short_name  AS section_short_name
                    FROM rf_subsection_sentence rfss
                        JOIN rf_sentence rs  ON rfss.rf_sentence_id = rs.id
                        JOIN rf_subsection r ON rfss.rf_subsection_id = r.id
                        JOIN rf_section s    ON r.rf_section_id = s.id
                    ORDER BY s.id, r.id, rfss.ord
                """)
                db.commit()
                return db.execute("SELECT COUNT(*) FROM view_rf_sentences").fetchone()[0]
        except Exception as e:
            print(f"Error refreshing view_rf_sentences: {str(e)}")
            return None

    def role_statements(self) -> list[tuple]:
        """(role, role name, subsection, statement id, statement) for each of the 227 role-statement rows."""
        return self._all("""
    SELECT sec.short_name, sec.full_name, sub.name, ss.rf_sentence_id, s.sentence
    FROM rf_subsection_sentence ss
    JOIN rf_subsection sub ON sub.id = ss.rf_subsection_id
    JOIN rf_section sec ON sec.id = sub.rf_section_id
    JOIN rf_sentence s ON s.id = ss.rf_sentence_id
""")

    def statement_texts(self, run_id: str | None = None) -> list[tuple]:
        """(statement id, statement), of one run when `run_id` is given."""
        if run_id is None:
            return self._all("SELECT id, sentence FROM rf_sentence")
        return self._all("SELECT id, sentence FROM rf_sentence WHERE run_id = ?", [run_id])

    def statement_subsections(self) -> list[tuple]:
        """(statement id, subsection) for each role-statement row."""
        return self._all("SELECT ss.rf_sentence_id, sub.name FROM rf_subsection_sentence ss "
                         "JOIN rf_subsection sub ON sub.id = ss.rf_subsection_id")

    def statement_roles(self) -> list[tuple]:
        """(role, statement id) for each role-statement row."""
        return self._all("SELECT sec.short_name, ss.rf_sentence_id FROM rf_subsection_sentence ss "
                         "JOIN rf_subsection sub ON sub.id = ss.rf_subsection_id "
                         "JOIN rf_section sec ON sec.id = sub.rf_section_id")

    def count_statements(self, run_id: str) -> int:
        return self._one("SELECT COUNT(*) FROM rf_sentence WHERE run_id = ?", [run_id])[0]

    def role_short_names(self) -> set[str]:
        """The short names of the stored roles."""
        return {name for (name,) in self._all("SELECT short_name FROM rf_section")}
