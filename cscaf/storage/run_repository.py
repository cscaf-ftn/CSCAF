"""The runs: the segmentation and embedding settings behind stored sentences and vectors."""


from cscaf.storage.repository import Repository


class RunRepository(Repository):
    """The runs: the segmentation and embedding settings behind stored sentences and vectors."""

    def ensure_run(self, run: dict) -> str | None:
        """
        Registers a run (the segmentation and embedding configuration) unless it already exists.

        A run is identified by its configuration (`cscaf.study.current_run`), so loading again
        with the same config.yaml reuses the existing row and keeps its original `created_at`.

        Returns:
            str | None: the run_id, or None on failure
        """
        columns = ("run_id", "created_at", "segmentation_engine", "segmentation_model", "segmentation_revision",
                   "embedding_model", "embedding_revision", "config_hash", "code_version", "notes")
        try:
            with self._connect() as db:
                db.execute(f"INSERT OR IGNORE INTO run ({', '.join(columns)}) "
                           f"VALUES ({', '.join('?' * len(columns))})", tuple(run.get(c) for c in columns))
                db.commit()
            return run["run_id"]
        except Exception as e:
            print(f"Error saving run: {str(e)}")
            return None
