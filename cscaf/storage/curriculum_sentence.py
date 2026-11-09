"""One sentence of a curriculum, the record the curriculum loader stores."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class CurriculumSentence:
    """One sentence of one course of a curriculum, with its embedding."""

    id: int | None
    ord: int
    syllabus_id: int
    syllabus_name: str
    curriculum_key: str
    sentence: str
    sentence_embedding: np.ndarray
    embedding_dim: int
    embedding_dtype: str
    embedding_model: str

    def __str__(self):
        return f"{self.curriculum_key}:{self.syllabus_name}:{self.sentence}"

    def __post_init__(self):
        if not self.curriculum_key or not self.syllabus_name or not self.sentence:
            raise ValueError("a curriculum sentence needs its curriculum key, course name and text")
