"""Loading of the raw data into the database: the framework, the curricula, the advertisements, the training
courses, and the similarities of their sentences to the ECSF statements (the notebooks of data_load/).

One subpackage per source; `LoadReport` is the base of every load report.
"""
from cscaf.loading.advertisements import AdvertisementLoader, AdvertisementLoadReport
from cscaf.loading.curricula import CurriculumLoader, CurriculumLoadReport, DuplicateCourses
from cscaf.loading.framework import FrameworkLoader
from cscaf.loading.load_report import LoadReport
from cscaf.loading.similarities import (AdvertisementSimilarities, AdvertisementSimilarityReport,
                                        CurriculumSimilarities, CurriculumSimilarityReport, SimilarityComputation)
from cscaf.loading.trainings import TrainingLoader, TrainingLoadReport

__all__ = ["AdvertisementLoadReport", "AdvertisementLoader", "AdvertisementSimilarities",
           "AdvertisementSimilarityReport", "CurriculumLoadReport", "CurriculumLoader", "CurriculumSimilarities",
           "CurriculumSimilarityReport", "DuplicateCourses", "FrameworkLoader", "LoadReport", "SimilarityComputation",
           "TrainingLoadReport", "TrainingLoader"]
