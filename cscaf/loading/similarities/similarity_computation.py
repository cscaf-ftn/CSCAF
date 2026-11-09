"""The similarity of every ECSF statement to every sentence of a run, and the best match of each statement.

Step 1 computes the cosine similarity of every pair (statement, sentence) from the stored embeddings and writes it to
the `_all` table of the source. The similarity is computed in float64 from the stored float32 vectors, each
normalised to unit length. Nothing is embedded again: the statements and the sentences must come from the same run,
hence the same embedding model.

Step 2 rebuilds the `_top_1` table (the best match of every statement in every curriculum or advertisement) from the
`_all` table by SQL and checks it against it. A curriculum or an advertisement that already has rows for the run is
skipped, so an interrupted computation can be resumed.
"""
from __future__ import annotations

import numpy as np


class SimilarityComputation:
    """The base of the similarity loaders: the run, the storage, the ECSF statements and the cosine matrix."""

    def __init__(self, storage, run_id: str):
        self.storage = storage
        self.run_id = run_id

    @staticmethod
    def cosine_similarity_matrix(rf_matrix: np.ndarray, sentence_matrix: np.ndarray) -> np.ndarray:
        """matrix[i, j] = cosine(statement i, sentence j), in float64."""
        rf = rf_matrix.astype(np.float64)
        sentences = sentence_matrix.astype(np.float64)
        rf /= np.linalg.norm(rf, axis=1, keepdims=True).clip(min=1e-12)
        sentences /= np.linalg.norm(sentences, axis=1, keepdims=True).clip(min=1e-12)
        return rf @ sentences.T

    def _statements(self) -> tuple[list[int], np.ndarray, str]:
        """The ids, the embedding matrix and the model of the ECSF statements of the run."""
        loaded = self.storage.framework.statement_embeddings(self.run_id)
        if loaded is None:
            raise Exception("Error reading the ECSF statements")
        rf_ids, rf_matrix, rf_model = loaded
        if not rf_ids:
            raise Exception(f"No ECSF statements for run {self.run_id}: load the reference framework first")
        return rf_ids, rf_matrix, rf_model
