"""Loading of the curricula (the notebook data_load/02)."""
from cscaf.loading.curricula.curriculum_load_report import CurriculumLoadReport
from cscaf.loading.curricula.curriculum_loader import CurriculumLoader
from cscaf.loading.curricula.duplicate_courses import DuplicateCourses

__all__ = ["CurriculumLoadReport", "CurriculumLoader", "DuplicateCourses"]
