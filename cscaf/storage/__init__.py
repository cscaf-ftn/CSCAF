"""The storage of the study: one SQLite database, one repository per part of the schema.

    storage = Storage.of(study)
    storage = Storage.of(study, read_only=False)
"""
from cscaf.storage.advertisement_repository import AdvertisementRepository
from cscaf.storage.country_repository import CountryRepository
from cscaf.storage.curriculum_repository import CurriculumRepository
from cscaf.storage.curriculum_sentence import CurriculumSentence
from cscaf.storage.database import Database
from cscaf.storage.framework_repository import FrameworkRepository
from cscaf.storage.repository import Repository
from cscaf.storage.run_repository import RunRepository
from cscaf.storage.similarity_repository import SimilarityRepository
from cscaf.storage.storage import Storage
from cscaf.storage.training_repository import TrainingRepository

__all__ = ["AdvertisementRepository", "CountryRepository", "CurriculumRepository", "CurriculumSentence", "Database",
           "FrameworkRepository", "Repository", "RunRepository", "SimilarityRepository", "Storage",
           "TrainingRepository"]
