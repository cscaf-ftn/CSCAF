"""One entry point for turning text into sentences and sentences into vectors (Section 3.3 of the paper).

    text -> preprocessing -> SaT -> item merge -> cleanup rules -> lead-in removal -> sentences
    sentences -> embeddings (all-mpnet-base-v2) -> cosine similarity to the ECSF statements

Every curriculum, advertisement and training course is split and embedded through this class, so all of them are
treated the same way. Every setting comes from `config.yaml` (`segmentation`, `model`). The ECSF statements are not
segmented: each is already one statement, so it only goes through `encode`.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

from cscaf.text.embedder import Embedder
from cscaf.text.sentence_segmenter import SentenceSegmenter


class TextPipeline:
    """Segmentation and embedding with the settings of a study."""

    def __init__(self, study, model: str | None = None):
        self.study = study
        self.config = study.config
        self.embedder = Embedder(self.config, model)

    @property
    def model_name(self) -> str:
        return self.embedder.model_name

    @property
    def embedding_dimension(self) -> int:
        return self.embedder.dimension

    @property
    def embedding_dtype(self) -> str:
        return self.embedder.dtype

    def sentences_with_dropped(self, text: str) -> tuple[list[str], list[str]]:
        """(kept, dropped) for one text; `dropped` holds what the cleanup rules removed."""
        return SentenceSegmenter.split_many([text or ""], config=self.config)[0]

    def sentences_many(self, texts: Sequence[str]) -> list[list[str]]:
        """Split several texts in one pass of the segmentation model; one list of sentences per text."""
        texts = [text or "" for text in texts]
        if not texts:
            return []
        return [kept for kept, _ in SentenceSegmenter.split_many(texts, config=self.config)]

    def document_sentences(self, parts: Sequence[str]) -> list[str]:
        """Split a document made of parts (an advertisement: title, then description), each part on its own."""
        return SentenceSegmenter.split_document(list(parts), config=self.config)

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        """float32 embeddings, one row per text, the form stored in the database."""
        return self.embedder.encode(texts)

    @staticmethod
    def similarity(sentence_embeddings: np.ndarray, statement_embeddings: np.ndarray) -> np.ndarray:
        """Cosine similarity of precomputed embeddings: matrix[i, j] = sim(sentence i, statement j)."""
        return Embedder.similarity_matrix(statement_embeddings, sentence_embeddings).T
