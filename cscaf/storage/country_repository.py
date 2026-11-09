"""The countries of the corpus."""


from cscaf.storage.repository import Repository


class CountryRepository(Repository):
    """The countries of the corpus."""

    def save_countries(self, countries: list[dict]) -> int | None:
        """
        Inserts the countries that are not in `country` yet, matched by name, in one transaction.

        Args:
            countries: [{"name", "is_eu", "is_efta"}], as in public_repo/raw_data/countries.json

        A curriculum and an advertisement are linked to their country by name (`get_country_id`), so the table
        is filled before either is loaded. A country already stored is left as it is.
        """
        try:
            with self._connect() as db:
                before = db.execute('SELECT COUNT(*) FROM country').fetchone()[0]
                db.executemany('INSERT INTO country (name, is_eu, is_efta) SELECT ?, ?, ? '
                               'WHERE NOT EXISTS (SELECT 1 FROM country WHERE name = ?)',
                               [(c["name"], int(c["is_eu"]), int(c["is_efta"]), c["name"]) for c in countries])
                db.commit()
                return db.execute('SELECT COUNT(*) FROM country').fetchone()[0] - before
        except Exception as e:
            print(f"Error saving the countries: {str(e)}")
            return None

    def country_id(self, name: str) -> int | None:
        try:
            with self._connect() as db:
                row = db.execute('SELECT id FROM country WHERE name = ?', (name,)).fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Error reading country {name}: {str(e)}")
            return None

    def countries(self) -> list[tuple[int, str, bool]] | None:
        try:
            with self._connect() as db:
                return [(row[0], row[1], bool(row[2]))
                        for row in db.execute('SELECT id, name, is_eu FROM country ORDER BY id')]
        except Exception as e:
            print(f"Error reading countries: {str(e)}")
            return None
