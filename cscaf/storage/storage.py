"""The storage of the study: one SQLite database, one repository per part of the schema.

    storage = Storage.of(study)
    storage = Storage.of(study, read_only=False)
"""
from __future__ import annotations

from pathlib import Path

from cscaf.storage.advertisement_repository import AdvertisementRepository
from cscaf.storage.country_repository import CountryRepository
from cscaf.storage.curriculum_repository import CurriculumRepository
from cscaf.storage.database import Database
from cscaf.storage.framework_repository import FrameworkRepository
from cscaf.storage.run_repository import RunRepository
from cscaf.storage.similarity_repository import SimilarityRepository
from cscaf.storage.training_repository import TrainingRepository


class Storage:
    """The repositories of one database."""

    def __init__(self, path: Path | str, read_only: bool = True):
        self.database = Database(path, read_only)
        self.framework = FrameworkRepository(self.database)
        self.countries = CountryRepository(self.database)
        self.curricula = CurriculumRepository(self.database)
        self.advertisements = AdvertisementRepository(self.database)
        self.trainings = TrainingRepository(self.database)
        self.similarities = SimilarityRepository(self.database)
        self.runs = RunRepository(self.database)

    @classmethod
    def of(cls, study, read_only: bool = True) -> "Storage":
        """The storage of the study's database."""
        return cls(study.database_path, read_only)

    @property
    def path(self) -> Path:
        return self.database.path

    def count_rows(self, table: str, run_id: str | None = None) -> int | None:
        return self.database.count_rows(table, run_id)
