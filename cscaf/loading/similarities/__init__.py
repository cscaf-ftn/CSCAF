"""The similarities of the curriculum and advertisement sentences to the ECSF statements (data_load/03 and 05)."""
from cscaf.loading.similarities.advertisement_similarities import AdvertisementSimilarities
from cscaf.loading.similarities.advertisement_similarity_report import AdvertisementSimilarityReport
from cscaf.loading.similarities.curriculum_similarities import CurriculumSimilarities
from cscaf.loading.similarities.curriculum_similarity_report import CurriculumSimilarityReport
from cscaf.loading.similarities.similarity_computation import SimilarityComputation

__all__ = ["AdvertisementSimilarities", "AdvertisementSimilarityReport", "CurriculumSimilarities",
           "CurriculumSimilarityReport", "SimilarityComputation"]
