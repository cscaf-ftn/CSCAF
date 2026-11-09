"""The industry training courses, their declared roles and their sentences."""

import numpy as np

from cscaf.storage.repository import Repository


class TrainingRepository(Repository):
    """The industry training courses, their declared roles and their sentences."""

    def training_id(self, code: str, variant: str) -> int | None:
        """
        The id of one (course code, extraction variant).

        Returns:
            int | None: the id, or None when that pair is not loaded or the read failed
        """
        try:
            with self._connect() as db:
                row = db.execute('SELECT id FROM industry_training WHERE code = ? AND variant = ?',
                                 (code, variant)).fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"Error reading industry_training id of {code}/{variant}: {str(e)}")
            return None

    def save_training(self, training: dict) -> int | None:
        """
        Inserts one course text with its provenance and the ECSF roles its provider assigns.

        The row and its roles are written in one transaction, so a course can never exist without the
        labels that selected it. The roles are checked against rf_section first: a label that is not an
        ECSF role short name is a mistake in the manifest and must stop the load, not be stored.

        Args:
            training: `code`, `title`, `source_description`, `source_url`, `accessed_date`, `variant`,
                `sections_taken`, `text`, optional `notes`, and `roles` as a list of rf_section
                short names

        Returns:
            int | None: the id of the new row, or None on failure
        """
        try:
            roles = list(dict.fromkeys(training.get("roles") or []))
            if not roles:
                raise ValueError(f"{training['code']}: at least one ECSF role must be given")
            with self._connect() as db:
                known = {r[0] for r in db.execute('SELECT short_name FROM rf_section').fetchall()}
                unknown = [r for r in roles if r not in known]
                if unknown:
                    raise ValueError(f"{training['code']}: not ECSF role short names: {unknown}")
                cursor = db.execute(
                    'INSERT INTO industry_training (code, title, source_description, source_url, '
                    'accessed_date, variant, sections_taken, text, notes) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (training["code"], training["title"], training["source_description"],
                     training["source_url"], training["accessed_date"], training["variant"],
                     training["sections_taken"], training["text"], training.get("notes")))
                training_id = cursor.lastrowid
                db.executemany('INSERT INTO industry_training_role (industry_training_id, '
                               'rf_section_short_name) VALUES (?, ?)',
                               [(training_id, role) for role in roles])
                db.commit()
            return training_id
        except Exception as e:
            print(f"Error saving industry training {training.get('code')}: {str(e)}")
            return None

    def replace_roles(self, code: str, roles: list[str]) -> int | None:
        """
        Replaces the ECSF roles of every stored variant of one course, in one transaction.

        Needed when the roles of a loaded course were recorded wrongly. The text is not touched. The roles are
        checked against rf_section, as on insertion.

        Returns:
            int | None: the number of role rows written, or None on failure (nothing is changed then)
        """
        try:
            roles = list(dict.fromkeys(roles))
            if not roles:
                raise ValueError(f"{code}: at least one ECSF role must be given")
            with self._connect() as db:
                known = {r[0] for r in db.execute('SELECT short_name FROM rf_section').fetchall()}
                unknown = [r for r in roles if r not in known]
                if unknown:
                    raise ValueError(f"{code}: not ECSF role short names: {unknown}")
                ids = [r[0] for r in db.execute('SELECT id FROM industry_training WHERE code = ?', (code,))]
                if not ids:
                    raise ValueError(f"{code} is not loaded")
                db.executemany('DELETE FROM industry_training_role WHERE industry_training_id = ?',
                               [(i,) for i in ids])
                db.executemany('INSERT INTO industry_training_role (industry_training_id, '
                               'rf_section_short_name) VALUES (?, ?)',
                               [(i, role) for i in ids for role in roles])
                db.commit()
            return len(ids) * len(roles)
        except Exception as e:
            print(f"Error replacing the roles of {code}: {str(e)}")
            return None

    def trainings(self, run_id: str | None = None) -> list[dict] | None:
        """
        Every loaded course with the roles its provider assigns and, for a run, its sentence count.

        Returns:
            list[dict] | None: one dict per (code, variant), ordered by code and variant
        """
        try:
            with self._connect() as db:
                rows = db.execute(
                    'SELECT t.id, t.code, t.title, t.source_description, t.source_url, t.accessed_date, '
                    '       t.variant, t.sections_taken, length(t.text), '
                    '       (SELECT group_concat(r.rf_section_short_name, ",") '
                    '          FROM industry_training_role r WHERE r.industry_training_id = t.id), '
                    '       (SELECT COUNT(*) FROM industry_training_sentence s '
                    '          WHERE s.industry_training_id = t.id AND (? IS NULL OR s.run_id = ?)) '
                    'FROM industry_training t ORDER BY t.code, t.variant', (run_id, run_id)).fetchall()
            return [{"id": r[0], "code": r[1], "title": r[2], "source_description": r[3],
                     "source_url": r[4], "accessed_date": r[5], "variant": r[6],
                     "sections_taken": r[7], "characters": r[8],
                     "roles": sorted((r[9] or "").split(",")) if r[9] else [],
                     "sentences": r[10]} for r in rows]
        except Exception as e:
            print(f"Error reading industry trainings: {str(e)}")
            return None

    def save_sentences(self, sentences: list[dict], run_id: str) -> int | None:
        """
        Inserts the sentences of one course, with their embeddings, in one transaction.

        Either every sentence is stored or none is, and each embedding is checked against its
        `embedding_dim` before it is written, as in save_curriculum_sentences.

        Args:
            sentences: dicts with `ord`, `industry_training_id`, `sentence` and the embedding fields
            run_id: the configuration that produced the sentences and the vectors

        Returns:
            int | None: the number stored, or None on failure
        """
        try:
            rows = []
            for s in sentences:
                blob = None
                embedding = s.get("sentence_embedding")
                if embedding is not None:
                    values = embedding.cpu().numpy() if hasattr(embedding, "cpu") else np.asarray(embedding)
                    np_emb = values.astype(np.dtype(s["embedding_dtype"])).reshape(-1)
                    if np_emb.size != s["embedding_dim"]:
                        raise ValueError(f"embedding of '{s['sentence'][:40]}' has {np_emb.size} values, "
                                         f"expected {s['embedding_dim']}")
                    blob = np_emb.tobytes()
                rows.append((run_id, s["ord"], s["industry_training_id"], s["sentence"], blob,
                             s["embedding_dim"] if blob is not None else None,
                             s["embedding_dtype"] if blob is not None else None,
                             s["embedding_model"] if blob is not None else None))
            with self._connect() as db:
                db.executemany(
                    'INSERT INTO industry_training_sentence (run_id, ord, industry_training_id, sentence, '
                    'sentence_embedding, embedding_dim, embedding_dtype, embedding_model) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?)', rows)
                db.commit()
            return len(rows)
        except Exception as e:
            print(f"Error saving industry training sentences: {str(e)}")
            return None

    def sentence_embeddings(self, industry_training_id: int, run_id: str) \
            -> tuple[list[tuple[int, int]], np.ndarray, str] | None:
        """(id, ord) rows, the embedding matrix and the model name, for one course and run."""
        try:
            with self._connect() as db:
                rows = db.execute('SELECT id, ord, sentence_embedding, embedding_dim, embedding_dtype, '
                                  'embedding_model FROM industry_training_sentence '
                                  'WHERE industry_training_id = ? AND run_id = ? ORDER BY ord',
                                  (industry_training_id, run_id)).fetchall()
            if not rows:
                return [], np.zeros((0, 0)), ""
            matrix, model = self._decode_embeddings([row[2:] for row in rows])
            return [row[:2] for row in rows], matrix, model
        except Exception as e:
            print(f"Error reading industry_training_sentence embeddings of {industry_training_id}: {str(e)}")
            return None

    def access_period(self) -> tuple:
        """(first, last) date the course pages were read."""
        return self._one("SELECT MIN(accessed_date), MAX(accessed_date) FROM industry_training")

    def count_courses(self) -> int:
        return self._one("SELECT COUNT(DISTINCT code) FROM industry_training")[0]

    def variant_counts(self) -> dict:
        """{extraction variant: number of courses}."""
        return dict(self._all("SELECT variant, COUNT(*) FROM industry_training GROUP BY variant"))

    def count_sentences(self, run_id: str, variant: str) -> int:
        return self._one(
            "SELECT COUNT(*) FROM industry_training_sentence s JOIN industry_training t ON t.id = s.industry_training_id "
            "WHERE s.run_id = ? AND t.variant = ?", [run_id, variant])[0]

    def of_variant(self, variant: str) -> list[tuple]:
        """(training id, code) of one extraction variant, by code."""
        return self._all("SELECT id, code FROM industry_training WHERE variant = ? ORDER BY code", [variant])

    def declared_roles(self, training_id: int) -> set[str]:
        """The ECSF roles the provider declares for one course."""
        return {role for (role,) in self._all("SELECT rf_section_short_name FROM industry_training_role "
                                               "WHERE industry_training_id = ?", [training_id])}

    def texts(self) -> list[tuple]:
        """(code, variant, text) of every stored course text, by code and variant."""
        return self._all("SELECT code, variant, text FROM industry_training ORDER BY code, variant")

    def text(self, training_id: int) -> str | None:
        row = self._one("SELECT text FROM industry_training WHERE id = ?", [int(training_id)])
        return row[0] if row else None
