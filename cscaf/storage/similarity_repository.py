"""The similarities of every sentence to every statement, and the best match of each statement."""

import json

import numpy as np

from cscaf.storage.repository import Repository


class SimilarityRepository(Repository):
    """The similarities of every sentence to every statement, and the best match of each statement."""

    def best_curriculum_matches(self, run_id: str, limit: int = 5) -> list[tuple] | None:
        try:
            with self._connect() as db:
                return db.execute('''
                    SELECT t.similarity_score, t.curriculum_key, t.curriculum_syllabus, r.sentence, c.sentence
                    FROM curriculum_rf_similarity_top_1 t
                        JOIN rf_sentence r ON r.id = t.rf_sentence_id
                        JOIN curriculum_sentence c ON c.id = t.curriculum_sentence_id
                    WHERE t.run_id = ? AND t.is_primary = 1
                    ORDER BY t.similarity_score DESC
                    LIMIT ?
                ''', (run_id, limit)).fetchall()
        except Exception as e:
            print(f"Error reading the best curriculum matches: {str(e)}")
            return None

    def count_curriculum_similarities(self, curriculum_id: int, run_id: str) -> int | None:
        try:
            with self._connect() as db:
                return db.execute('SELECT COUNT(*) FROM curriculum_rf_similarity_all '
                                  'WHERE curriculum_id = ? AND run_id = ?', (curriculum_id, run_id)).fetchone()[0]
        except Exception as e:
            print(f"Error counting curriculum_rf_similarity_all of curriculum {curriculum_id}: {str(e)}")
            return None

    def save_curriculum_similarities(self, rows: list[tuple]) -> int | None:
        """
        Inserts the pairs of one curriculum in one transaction: either all rows are stored or none.

        Args:
            rows: (run_id, rf_sentence_id, curriculum_sentence_id, similarity_score, curriculum_id,
                curriculum_key, syllabus_id, curriculum_syllabus) per pair

        Returns:
            int | None: the number of rows stored, or None on failure
        """
        try:
            with self._connect() as db:
                db.executemany(
                    'INSERT INTO curriculum_rf_similarity_all (run_id, rf_sentence_id, curriculum_sentence_id, '
                    'similarity_score, curriculum_id, curriculum_key, syllabus_id, curriculum_syllabus) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?)', rows)
                db.commit()
            return len(rows)
        except Exception as e:
            print(f"Error saving curriculum_rf_similarity_all: {str(e)}")
            return None

    def refresh_curriculum_best_matches(self, run_id: str) -> int | None:
        """
        Rebuilds curriculum_rf_similarity_top_1 of one run from curriculum_rf_similarity_all.

        Per (curriculum, ECSF statement), the pair with the highest score is the primary row
        (is_primary = 1; the lowest curriculum_sentence_id wins an exact tie), so C(s) read from
        the primary rows equals the maximum in the _all table. Every other sentence of the same
        curriculum whose text equals the primary sentence's text is added with is_primary = 0:
        the text stands in several courses and each of them is credited. Identical texts are
        matched by text, because their scores can differ by about 1e-7.

        The rows of the run are deleted and rebuilt in one transaction; other runs are untouched.

        Returns:
            int | None: the number of rows of the run afterwards, or None on failure
        """
        try:
            with self._connect() as db:
                db.execute('DELETE FROM curriculum_rf_similarity_top_1 WHERE run_id = ?', (run_id,))
                db.execute('''
                    WITH ranked AS (
                        SELECT a.*, cs.sentence AS sentence_text,
                               ROW_NUMBER() OVER (PARTITION BY a.curriculum_id, a.rf_sentence_id
                                                  ORDER BY a.similarity_score DESC, a.curriculum_sentence_id) AS rank
                        FROM curriculum_rf_similarity_all a
                            JOIN curriculum_sentence cs ON cs.id = a.curriculum_sentence_id
                        WHERE a.run_id = ?
                    ),
                    best AS (
                        SELECT curriculum_id, rf_sentence_id, sentence_text FROM ranked WHERE rank = 1
                    )
                    INSERT INTO curriculum_rf_similarity_top_1 (run_id, rf_sentence_id, curriculum_sentence_id,
                                                                similarity_score, curriculum_id, curriculum_key,
                                                                syllabus_id, curriculum_syllabus, is_primary)
                    SELECT r.run_id, r.rf_sentence_id, r.curriculum_sentence_id, r.similarity_score,
                           r.curriculum_id, r.curriculum_key, r.syllabus_id, r.curriculum_syllabus,
                           CASE WHEN r.rank = 1 THEN 1 ELSE 0 END
                    FROM ranked r
                        JOIN best b ON b.curriculum_id = r.curriculum_id
                                   AND b.rf_sentence_id = r.rf_sentence_id
                                   AND b.sentence_text = r.sentence_text
                    ORDER BY r.curriculum_id, r.rf_sentence_id, r.rank
                ''', (run_id,))
                db.commit()
                return db.execute('SELECT COUNT(*) FROM curriculum_rf_similarity_top_1 WHERE run_id = ?',
                                  (run_id,)).fetchone()[0]
        except Exception as e:
            print(f"Error refreshing curriculum_rf_similarity_top_1: {str(e)}")
            return None

    def check_curriculum_best_matches(self, run_id: str) -> dict | None:
        """
        Counts that show whether the top_1 table of a run agrees with the _all table.

        Returns:
            dict | None: `pairs_in_all` (distinct curriculum-statement pairs in _all), `primary_rows`,
            `primary_not_max` (primary rows whose score is not the pair's maximum in _all; must be 0),
            `other_text` (rows whose text differs from their primary row's text; must be 0),
            `rows` (all rows of the run in top_1)
        """
        try:
            with self._connect() as db:
                pairs_in_all = db.execute('SELECT COUNT(*) FROM (SELECT DISTINCT curriculum_id, rf_sentence_id '
                                          'FROM curriculum_rf_similarity_all WHERE run_id = ?)',
                                          (run_id,)).fetchone()[0]
                primary_rows = db.execute('SELECT COUNT(*) FROM curriculum_rf_similarity_top_1 '
                                          'WHERE run_id = ? AND is_primary = 1', (run_id,)).fetchone()[0]
                primary_not_max = db.execute('''
                    SELECT COUNT(*) FROM curriculum_rf_similarity_top_1 t
                        JOIN (SELECT curriculum_id, rf_sentence_id, MAX(similarity_score) AS best
                              FROM curriculum_rf_similarity_all WHERE run_id = ?
                              GROUP BY curriculum_id, rf_sentence_id) m
                          ON m.curriculum_id = t.curriculum_id AND m.rf_sentence_id = t.rf_sentence_id
                    WHERE t.run_id = ? AND t.is_primary = 1 AND t.similarity_score <> m.best
                ''', (run_id, run_id)).fetchone()[0]
                other_text = db.execute('''
                    SELECT COUNT(*) FROM curriculum_rf_similarity_top_1 t
                        JOIN curriculum_rf_similarity_top_1 p
                          ON p.run_id = t.run_id AND p.curriculum_id = t.curriculum_id
                         AND p.rf_sentence_id = t.rf_sentence_id AND p.is_primary = 1
                        JOIN curriculum_sentence ts ON ts.id = t.curriculum_sentence_id
                        JOIN curriculum_sentence ps ON ps.id = p.curriculum_sentence_id
                    WHERE t.run_id = ? AND ts.sentence <> ps.sentence
                ''', (run_id,)).fetchone()[0]
                rows = db.execute('SELECT COUNT(*) FROM curriculum_rf_similarity_top_1 WHERE run_id = ?',
                                  (run_id,)).fetchone()[0]
                return {"pairs_in_all": pairs_in_all, "primary_rows": primary_rows,
                        "primary_not_max": primary_not_max, "other_text": other_text, "rows": rows}
        except Exception as e:
            print(f"Error checking curriculum_rf_similarity_top_1: {str(e)}")
            return None

    def refresh_course_best_matches(self, run_id: str) -> int | None:
        """
        Rebuilds curriculum_syllabus_rf_top_1 of one run from curriculum_rf_similarity_all.

        Per (syllabus, ECSF statement) it keeps the pair with the highest score, the lowest sentence id
        winning an exact tie. The rows of the run are deleted and rebuilt in one transaction.

        Returns:
            int | None: the number of rows of the run afterwards, or None on failure
        """
        try:
            with self._connect() as db:
                db.execute('DELETE FROM curriculum_syllabus_rf_top_1 WHERE run_id = ?', (run_id,))
                db.execute('''
                    INSERT INTO curriculum_syllabus_rf_top_1 (run_id, rf_sentence_id, curriculum_sentence_id,
                        similarity_score, curriculum_id, curriculum_key, syllabus_id, curriculum_syllabus)
                    SELECT ?, r.rf_sentence_id, r.curriculum_sentence_id, r.similarity_score, r.curriculum_id,
                           r.curriculum_key, r.syllabus_id, r.curriculum_syllabus
                    FROM (
                        SELECT a.rf_sentence_id, a.curriculum_sentence_id, a.similarity_score, a.curriculum_id,
                               a.curriculum_key, a.syllabus_id, a.curriculum_syllabus,
                               ROW_NUMBER() OVER (PARTITION BY a.syllabus_id, a.rf_sentence_id
                                                  ORDER BY a.similarity_score DESC,
                                                           a.curriculum_sentence_id) AS rank
                        FROM curriculum_rf_similarity_all a
                        WHERE a.run_id = ?
                    ) r
                    WHERE r.rank = 1
                ''', (run_id, run_id))
                db.commit()
                return db.execute('SELECT COUNT(*) FROM curriculum_syllabus_rf_top_1 WHERE run_id = ?',
                                  (run_id,)).fetchone()[0]
        except Exception as e:
            print(f"Error refreshing curriculum_syllabus_rf_top_1: {str(e)}")
            return None

    def curriculum_item_scores(self, run_id: str, curriculum_keys: list[str] | None = None) -> list[tuple] | None:
        """The best match per (curriculum, statement): the primary rows of curriculum_rf_similarity_top_1."""
        try:
            with self._connect() as db:
                query = ('SELECT t.curriculum_key, c.country, t.rf_sentence_id, t.similarity_score '
                         'FROM curriculum_rf_similarity_top_1 t JOIN curriculum c ON c.id = t.curriculum_id '
                         'WHERE t.run_id = ? AND t.is_primary = 1')
                arguments = [run_id]
                if curriculum_keys is not None:
                    query += ' AND t.curriculum_key IN (SELECT value FROM json_each(?))'
                    arguments.append(json.dumps(list(curriculum_keys)))
                return db.execute(query + ' ORDER BY t.curriculum_key, t.rf_sentence_id', arguments).fetchall()
        except Exception as e:
            print(f"Error reading the curriculum item scores: {str(e)}")
            return None

    def course_item_scores(self, run_id: str, curriculum_keys: list[str] | None = None) -> list[tuple] | None:
        try:
            with self._connect() as db:
                query = ('SELECT curriculum_key, syllabus_id, curriculum_syllabus, rf_sentence_id, similarity_score '
                         'FROM curriculum_syllabus_rf_top_1 WHERE run_id = ?')
                arguments = [run_id]
                if curriculum_keys is not None:
                    query += ' AND curriculum_key IN (SELECT value FROM json_each(?))'
                    arguments.append(json.dumps(list(curriculum_keys)))
                return db.execute(query + ' ORDER BY curriculum_key, syllabus_id, rf_sentence_id',
                                  arguments).fetchall()
        except Exception as e:
            print(f"Error reading the syllabus item scores: {str(e)}")
            return None

    def advertisement_item_scores(self, run_id: str, countries: list[str] | None = None,
                                           date_from: str | None = None, date_to: str | None = None) \
            -> tuple[int, list[tuple]] | None:
        """
        The best match per (ad, statement) for a set of ads, and the size N of that set.

        N counts every ad of the set, including ads whose best match is far below the threshold: that
        is what makes D(s) and B(s) fall as unrelated ads are added (Equation (4) of the paper).

        N is counted from the advertisements, never from the rows of the match table. An ad that
        matches nothing may have no row there, and a count taken from the table would silently drop
        exactly the ads that make the correction work. The ads counted are those of the set that are
        in the corpus of this run: an ad left with no sentence after the cleanup rules is not.
        """
        try:
            ad_conditions, ad_arguments = [], []
            if countries is not None:
                ad_conditions.append('ja.country IN (SELECT value FROM json_each(?))')
                ad_arguments.append(json.dumps(list(countries)))
            if date_from is not None:
                ad_conditions.append('ja.date_posted >= ?')
                ad_arguments.append(date_from)
            if date_to is not None:
                ad_conditions.append('ja.date_posted <= ?')
                ad_arguments.append(date_to)
            in_corpus = ('EXISTS (SELECT 1 FROM job_advertisement_sentence s '
                         'WHERE s.run_id = ? AND s.job_advertisement_id = ja.id)')
            count_where = ' AND '.join([in_corpus, *ad_conditions])
            rows_where = ' AND '.join(['t.run_id = ?', *ad_conditions])
            with self._connect() as db:
                ads = db.execute(f'SELECT COUNT(*) FROM job_advertisement ja WHERE {count_where}',
                                 [run_id, *ad_arguments]).fetchone()[0]
                rows = db.execute(f'SELECT t.job_advertisement_id, t.rf_sentence_id, t.similarity_score '
                                  f'FROM job_advertisement_rf_similarity_top_1 t '
                                  f'JOIN job_advertisement ja ON ja.id = t.job_advertisement_id '
                                  f'WHERE {rows_where}', [run_id, *ad_arguments]).fetchall()
            return ads, rows
        except Exception as e:
            print(f"Error reading the job advertisement item scores: {str(e)}")
            return None

    def curriculum_best_match_sentences(self, run_id: str) -> list[tuple] | None:
        try:
            with self._connect() as db:
                return db.execute('''
                    SELECT t.rf_sentence_id, r.sentence, t.curriculum_sentence_id, c.sentence, t.similarity_score,
                           t.curriculum_key, t.curriculum_syllabus
                    FROM curriculum_rf_similarity_top_1 t
                        JOIN rf_sentence r ON r.id = t.rf_sentence_id
                        JOIN curriculum_sentence c ON c.id = t.curriculum_sentence_id
                    WHERE t.run_id = ? AND t.is_primary = 1
                    ORDER BY t.curriculum_id, t.rf_sentence_id
                ''', (run_id,)).fetchall()
        except Exception as e:
            print(f"Error reading curriculum best matches: {str(e)}")
            return None

    def save_advertisement_similarities(self, rows: list[tuple]) -> int | None:
        try:
            with self._connect() as db:
                db.executemany('INSERT INTO job_advertisement_rf_similarity_all (job_advertisement_sentence_id, '
                               'rf_sentence_id, similarity_score) VALUES (?, ?, ?)', rows)
                db.commit()
            return len(rows)
        except Exception as e:
            print(f"Error saving job_advertisement_rf_similarity_all: {str(e)}")
            return None

    def count_advertisement_similarities(self, run_id: str) -> int | None:
        try:
            with self._connect() as db:
                return db.execute('''
                    SELECT COUNT(*) FROM job_advertisement_rf_similarity_all a
                        JOIN job_advertisement_sentence s ON s.id = a.job_advertisement_sentence_id
                    WHERE s.run_id = ?
                ''', (run_id,)).fetchone()[0]
        except Exception as e:
            print(f"Error counting job_advertisement_rf_similarity_all: {str(e)}")
            return None

    def advertisement_similarity_sample(self, run_id: str, size: int, seed: int) -> list[tuple] | None:
        """
        Draws about `size` random rows of the _all table of a run, with both stored vectors, so that
        a score can be recomputed independently. Ids are drawn uniformly up to the largest id; ids of
        another run are skipped, so fewer rows may come back.
        """
        try:
            with self._connect() as db:
                largest = db.execute('SELECT MAX(id) FROM job_advertisement_rf_similarity_all').fetchone()[0]
                if not largest:
                    return []
                ids = sorted(set(np.random.default_rng(seed).integers(1, largest + 1, size).tolist()))
                rows = db.execute('''
                    SELECT a.similarity_score, r.sentence_embedding, r.embedding_dtype,
                           s.sentence_embedding, s.embedding_dtype
                    FROM job_advertisement_rf_similarity_all a
                        JOIN rf_sentence r ON r.id = a.rf_sentence_id
                        JOIN job_advertisement_sentence s ON s.id = a.job_advertisement_sentence_id
                    WHERE a.id IN (SELECT value FROM json_each(?)) AND s.run_id = ?
                ''', (json.dumps(ids), run_id)).fetchall()
            return [(score, np.frombuffer(rf_blob, dtype=np.dtype(rf_dtype)),
                     np.frombuffer(sentence_blob, dtype=np.dtype(sentence_dtype)))
                    for score, rf_blob, rf_dtype, sentence_blob, sentence_dtype in rows]
        except Exception as e:
            print(f"Error sampling job_advertisement_rf_similarity_all: {str(e)}")
            return None

    def refresh_advertisement_best_matches(self, run_id: str, ads_per_step: int = 500) -> int | None:
        """
        Rebuilds job_advertisement_rf_similarity_top_1 of one run from job_advertisement_rf_similarity_all.

        Per (ad, ECSF statement) the pair with the highest score is kept, the lowest sentence id winning
        an exact tie; this is the best-match similarity of Equation (1). An ad stores an identical
        sentence only once, so there are no ties by text. The rows of the run are deleted and rebuilt in
        one transaction, in steps of `ads_per_step` ads to keep each sort small; other runs are untouched.

        Returns:
            int | None: the number of rows of the run afterwards, or None on failure
        """
        try:
            with self._connect() as db:
                ad_ids = [row[0] for row in db.execute(
                    'SELECT DISTINCT job_advertisement_id FROM job_advertisement_sentence WHERE run_id = ? '
                    'ORDER BY job_advertisement_id', (run_id,))]
                db.execute('DELETE FROM job_advertisement_rf_similarity_top_1 WHERE run_id = ?', (run_id,))
                for start in range(0, len(ad_ids), ads_per_step):
                    step = ad_ids[start:start + ads_per_step]
                    db.execute('''
                        INSERT INTO job_advertisement_rf_similarity_top_1 (run_id, rf_sentence_id,
                            job_advertisement_sentence_id, similarity_score, job_advertisement_id, job_key,
                            country_id, part)
                        SELECT ?, r.rf_sentence_id, r.job_advertisement_sentence_id, r.similarity_score,
                               r.job_advertisement_id, ja.job_key, ja.country_id, r.part
                        FROM (
                            SELECT a.rf_sentence_id, a.job_advertisement_sentence_id, a.similarity_score,
                                   s.job_advertisement_id, s.part,
                                   ROW_NUMBER() OVER (PARTITION BY s.job_advertisement_id, a.rf_sentence_id
                                                      ORDER BY a.similarity_score DESC,
                                                               a.job_advertisement_sentence_id) AS rank
                            FROM job_advertisement_sentence s
                                JOIN job_advertisement_rf_similarity_all a ON a.job_advertisement_sentence_id = s.id
                            WHERE s.run_id = ? AND s.job_advertisement_id BETWEEN ? AND ?
                        ) r
                            JOIN job_advertisement ja ON ja.id = r.job_advertisement_id
                        WHERE r.rank = 1
                    ''', (run_id, run_id, step[0], step[-1]))
                db.commit()
                return db.execute('SELECT COUNT(*) FROM job_advertisement_rf_similarity_top_1 WHERE run_id = ?',
                                  (run_id,)).fetchone()[0]
        except Exception as e:
            print(f"Error refreshing job_advertisement_rf_similarity_top_1: {str(e)}")
            return None

    def check_advertisement_best_matches(self, run_id: str) -> dict | None:
        """
        Counts that show whether the similarity tables of a run are complete and agree.

        Returns:
            dict | None: `statements`, `ads`, `sentences` of the run; `all_rows` (must equal
            statements x sentences); `top_1_rows` (must equal statements x ads); `not_max` (top_1 rows
            whose score is not the pair's maximum in _all; must be 0); `wrong_sentence` (top_1 rows whose
            sentence belongs to another ad or run; must be 0)
        """
        try:
            with self._connect() as db:
                one = lambda query, *args: db.execute(query, args).fetchone()[0]
                result = {
                    "statements": one('SELECT COUNT(*) FROM rf_sentence WHERE run_id = ?', run_id),
                    "ads": one('SELECT COUNT(DISTINCT job_advertisement_id) FROM job_advertisement_sentence '
                               'WHERE run_id = ?', run_id),
                    "sentences": one('SELECT COUNT(*) FROM job_advertisement_sentence WHERE run_id = ?', run_id),
                    "all_rows": one('SELECT COUNT(*) FROM job_advertisement_rf_similarity_all a '
                                    'JOIN job_advertisement_sentence s ON s.id = a.job_advertisement_sentence_id '
                                    'WHERE s.run_id = ?', run_id),
                    "top_1_rows": one('SELECT COUNT(*) FROM job_advertisement_rf_similarity_top_1 WHERE run_id = ?',
                                      run_id),
                    "not_max": one('''
                        SELECT COUNT(*) FROM job_advertisement_rf_similarity_top_1 t
                            JOIN (SELECT s.job_advertisement_id, a.rf_sentence_id, MAX(a.similarity_score) AS best
                                  FROM job_advertisement_sentence s
                                      JOIN job_advertisement_rf_similarity_all a
                                        ON a.job_advertisement_sentence_id = s.id
                                  WHERE s.run_id = ?
                                  GROUP BY s.job_advertisement_id, a.rf_sentence_id) m
                              ON m.job_advertisement_id = t.job_advertisement_id AND m.rf_sentence_id = t.rf_sentence_id
                        WHERE t.run_id = ? AND t.similarity_score <> m.best
                    ''', run_id, run_id),
                    "wrong_sentence": one('''
                        SELECT COUNT(*) FROM job_advertisement_rf_similarity_top_1 t
                            JOIN job_advertisement_sentence s ON s.id = t.job_advertisement_sentence_id
                        WHERE t.run_id = ? AND (s.job_advertisement_id <> t.job_advertisement_id OR s.run_id <> t.run_id)
                    ''', run_id),
                }
                return result
        except Exception as e:
            print(f"Error checking job_advertisement_rf_similarity_top_1: {str(e)}")
            return None

    def save_training_similarities(self, rows: list[tuple]) -> int | None:
        """
        Inserts (run_id, rf_sentence_id, industry_training_sentence_id, score, training_id, code) rows.

        Returns:
            int | None: the number of rows stored, or None on failure
        """
        try:
            with self._connect() as db:
                db.executemany(
                    'INSERT INTO industry_training_rf_similarity_all (run_id, rf_sentence_id, '
                    'industry_training_sentence_id, similarity_score, industry_training_id, '
                    'industry_training_code) VALUES (?, ?, ?, ?, ?, ?)', rows)
                db.commit()
            return len(rows)
        except Exception as e:
            print(f"Error saving industry training similarities: {str(e)}")
            return None

    def refresh_training_best_matches(self, run_id: str) -> int | None:
        """
        Rebuilds industry_training_rf_similarity_top_1 of one run from the _all table.

        Per (course, ECSF statement) the pair with the highest score is the primary row (is_primary = 1;
        the lowest sentence id wins an exact tie), so the best match read from the primary rows equals
        the maximum in the _all table. Every other sentence of the same course whose text equals the
        primary sentence's text is added with is_primary = 0, matched by text because identical texts
        can differ in score by about 1e-7. This mirrors refresh_curriculum_rf_similarity_top_1.

        The rows of the run are deleted and rebuilt in one transaction; other runs are untouched.

        Returns:
            int | None: the number of rows of the run afterwards, or None on failure
        """
        try:
            with self._connect() as db:
                db.execute('DELETE FROM industry_training_rf_similarity_top_1 WHERE run_id = ?', (run_id,))
                db.execute("""
                    WITH ranked AS (
                        SELECT a.*, s.sentence AS sentence_text,
                               ROW_NUMBER() OVER (PARTITION BY a.industry_training_id, a.rf_sentence_id
                                                  ORDER BY a.similarity_score DESC,
                                                           a.industry_training_sentence_id) AS rank
                        FROM industry_training_rf_similarity_all a
                            JOIN industry_training_sentence s
                              ON s.id = a.industry_training_sentence_id
                        WHERE a.run_id = ?
                    ),
                    best AS (
                        SELECT industry_training_id, rf_sentence_id, sentence_text
                        FROM ranked WHERE rank = 1
                    )
                    INSERT INTO industry_training_rf_similarity_top_1
                        (run_id, rf_sentence_id, industry_training_sentence_id, similarity_score,
                         industry_training_id, industry_training_code, is_primary)
                    SELECT r.run_id, r.rf_sentence_id, r.industry_training_sentence_id, r.similarity_score,
                           r.industry_training_id, r.industry_training_code,
                           CASE WHEN r.rank = 1 THEN 1 ELSE 0 END
                    FROM ranked r
                        JOIN best b ON b.industry_training_id = r.industry_training_id
                                   AND b.rf_sentence_id = r.rf_sentence_id
                                   AND b.sentence_text = r.sentence_text
                    ORDER BY r.industry_training_id, r.rf_sentence_id, r.rank
                """, (run_id,))
                db.commit()
                return db.execute('SELECT COUNT(*) FROM industry_training_rf_similarity_top_1 '
                                  'WHERE run_id = ?', (run_id,)).fetchone()[0]
        except Exception as e:
            print(f"Error refreshing industry_training_rf_similarity_top_1: {str(e)}")
            return None

    def training_item_scores(self, run_id: str, codes: list[str] | None = None) \
            -> list[tuple] | None:
        """
        The best match per (course, ECSF statement): the best-match similarity of Equation (1) for a course text.

        Args:
            run_id: the run to read
            codes: course codes to restrict to, or None for every loaded course

        Returns:
            list[tuple] | None: (code, variant, rf_sentence_id, similarity_score, sentence) with one
            row per course and statement, ordered by code, variant and statement
        """
        try:
            query = ('SELECT t.code, t.variant, p.rf_sentence_id, p.similarity_score, s.sentence '
                     'FROM industry_training_rf_similarity_top_1 p '
                     '    JOIN industry_training t ON t.id = p.industry_training_id '
                     '    JOIN industry_training_sentence s ON s.id = p.industry_training_sentence_id '
                     'WHERE p.run_id = ? AND p.is_primary = 1')
            parameters: list = [run_id]
            if codes:
                query += f" AND t.code IN ({','.join('?' * len(codes))})"
                parameters += list(codes)
            query += ' ORDER BY t.code, t.variant, p.rf_sentence_id'
            with self._connect() as db:
                return db.execute(query, parameters).fetchall()
        except Exception as e:
            print(f"Error reading industry training item scores: {str(e)}")
            return None

    def count_curriculum_best_matches(self, run_id: str) -> int:
        return self._one("SELECT COUNT(*) FROM curriculum_rf_similarity_top_1 WHERE run_id = ? AND is_primary = 1",
                         [run_id])[0]

    def count_advertisement_best_matches(self, run_id: str) -> int:
        return self._one("SELECT COUNT(*) FROM job_advertisement_rf_similarity_top_1 WHERE run_id = ?", [run_id])[0]

    def statements_covered_per_curriculum(self, run_id: str, threshold: float) -> dict:
        """{curriculum key: statements whose best match reaches `threshold`}; a curriculum with none is absent."""
        return dict(self._all(
            "SELECT curriculum_key, COUNT(DISTINCT rf_sentence_id) FROM curriculum_rf_similarity_top_1 "
            "WHERE run_id = ? AND is_primary = 1 AND similarity_score >= ? GROUP BY curriculum_key", [run_id, threshold]))

    def advertisements_with_statement(self, run_id: str, threshold: float) -> int:
        """Advertisements in which at least one statement reaches `threshold`."""
        return self._one(
            "SELECT COUNT(DISTINCT job_advertisement_id) FROM job_advertisement_rf_similarity_top_1 "
            "WHERE run_id = ? AND similarity_score >= ?", [run_id, threshold])[0]

    def curriculum_best_match_rows(self, run_id: str) -> list[tuple]:
        """(curriculum key, statement id, curriculum sentence id, similarity) of every best match."""
        return self._all("SELECT curriculum_key, rf_sentence_id, curriculum_sentence_id, similarity_score "
                         "FROM curriculum_rf_similarity_top_1 WHERE run_id = ? AND is_primary = 1", [run_id])

    def curriculum_matches_above(self, run_id: str, threshold: float) -> list[tuple]:
        """(curriculum key, statement id, curriculum sentence id) of every sentence that reaches `threshold`."""
        return self._all("SELECT curriculum_key, rf_sentence_id, curriculum_sentence_id FROM curriculum_rf_similarity_all "
                         "WHERE run_id = ? AND similarity_score >= ?", [run_id, threshold])

    def advertisement_sentences_for_statement(self, statement: str, threshold: float) -> list[tuple]:
        """(sentence,) of every advertisement whose best match for the statement reaches `threshold`."""
        return self._all("SELECT s.sentence FROM job_advertisement_rf_similarity_top_1 t "
                         "JOIN rf_sentence r ON r.id = t.rf_sentence_id "
                         "JOIN job_advertisement_sentence s ON s.id = t.job_advertisement_sentence_id "
                         "WHERE r.sentence = ? AND t.similarity_score >= ?", (statement, threshold))

    def training_statements_above(self, training_id: int, threshold: float) -> set[int]:
        """The statements whose best match in one training course reaches `threshold`."""
        return {s for (s,) in self._all("SELECT DISTINCT rf_sentence_id FROM industry_training_rf_similarity_top_1 "
                                        "WHERE industry_training_id = ? AND is_primary = 1 AND similarity_score >= ?",
                                        [training_id, threshold])}

    def advertisement_best_match_rows(self, run_id: str) -> list[tuple]:
        """(advertisement id, statement id, similarity, advertisement sentence id) of every best match."""
        return self._all("SELECT job_advertisement_id, rf_sentence_id, similarity_score, job_advertisement_sentence_id "
                         "FROM job_advertisement_rf_similarity_top_1 WHERE run_id = ?", [run_id])

    def count_training_similarities(self, run_id: str, training_id: int) -> int:
        return self._one("SELECT COUNT(*) FROM industry_training_rf_similarity_all "
                         "WHERE run_id = ? AND industry_training_id = ?", [run_id, int(training_id)])[0]

    def count_training_best_matches(self, run_id: str) -> int:
        return self._one("SELECT COUNT(*) FROM industry_training_rf_similarity_top_1 "
                         "WHERE run_id = ? AND is_primary = 1", [run_id])[0]
