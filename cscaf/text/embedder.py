"""Sentence embeddings with the model of `config.yaml` `model` (Section 3.3 of the paper).

The model is named and pinned to a Hugging Face revision in `config.yaml`; `device: cuda` means cuda, with no silent
fallback to the CPU. Loaded models are cached per (name, revision, device), so asking for a second model never
returns the first.

The `all-*` sentence-transformers checkpoints end with a Normalize module, so `encode` returns unit-length vectors.
They are stored in the database as float32 exactly as returned.
"""
from __future__ import annotations

import threading
from typing import Any, ClassVar, Sequence

import numpy as np


class Embedder:
    """Encodes texts with one sentence-transformers model of `config.yaml`."""

    DEFAULT: ClassVar[str] = "default"
    _models: ClassVar[dict[tuple[str, str, str], Any]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self, config: dict, model: str | None = None):
        self._config = config
        self._alias = model
        self._transformer = None

    @classmethod
    def resolve(cls, config: dict, model: str | None = None) -> tuple[str, str | None]:
        """(name, revision) of an alias or a model id; None or "default" is the model of the study.

        Aliases come from `model.registry`; a full model id is accepted only if it is in the registry, so that every
        model used has a recorded revision.
        """
        settings = config["model"]
        registry = settings.get("registry", {})
        if model in (None, cls.DEFAULT):
            return settings["name"], settings.get("revision")
        if model in registry:
            entry = registry[model]
            return entry["name"], entry.get("revision")
        for entry in registry.values():
            if entry["name"] == model:
                return entry["name"], entry.get("revision")
        raise ValueError(f"Unknown model {model!r}. Add it to config.yaml `model.registry` with its Hugging Face "
                         f"revision; known aliases: {sorted(registry)}")

    @classmethod
    def _load(cls, name: str, revision: str | None, device: str):
        """Load one model. Called under the lock, never directly."""
        import torch
        from sentence_transformers import SentenceTransformer

        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError(f"config.yaml requests device {device!r}, but no CUDA GPU is available")
        if revision is None:
            raise ValueError(f"{name} has no revision in config.yaml `model.registry`; pin it before use")
        return SentenceTransformer(name, device=device, revision=revision)

    @property
    def transformer(self):
        if self._transformer is None:
            name, revision = self.resolve(self._config, self._alias)
            device = self._config["model"].get("device", "cuda")
            key = (name, revision or "", device)
            with self._lock:
                if key not in self._models:
                    self._models[key] = self._load(name, revision, device)
            self._transformer = self._models[key]
        return self._transformer

    @property
    def model_name(self) -> str:
        """The name of the model, as stored with every vector."""
        return self.resolve(self._config, self._alias)[0]

    @property
    def dimension(self) -> int:
        """The length of the vectors, asked from the model itself (768 for all-mpnet-base-v2)."""
        return int(self.transformer.get_sentence_embedding_dimension())

    @property
    def dtype(self) -> str:
        """The numpy dtype in which vectors are stored (`model.embedding_dtype`)."""
        return self._config["model"].get("embedding_dtype", "float32")

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        """float32 vectors, one row per text."""
        texts = list(texts)
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        return self.transformer.encode(texts, convert_to_numpy=True, show_progress_bar=False,
                                       batch_size=self._config["model"].get("batch_size", 32)).astype(np.float32)

    @staticmethod
    def as_matrix(embeddings) -> np.ndarray:
        """A list of tensors, a list of arrays or a 2-D array, as one float32 array."""
        if isinstance(embeddings, np.ndarray):
            return embeddings.astype(np.float32, copy=False)
        rows = [np.asarray(e.cpu() if hasattr(e, "cpu") else e, dtype=np.float32).reshape(-1) for e in embeddings]
        if not rows:
            return np.zeros((0, 0), dtype=np.float32)
        return np.vstack(rows)

    @staticmethod
    def cosine(embedding1, embedding2) -> float:
        """The cosine similarity of two vectors."""
        a = Embedder.as_matrix([embedding1])[0]
        b = Embedder.as_matrix([embedding2])[0]
        if a.shape != b.shape:
            raise ValueError(f"Embedding dimensions mismatch: {a.shape} vs {b.shape}")
        denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
        return 0.0 if denominator == 0 else float(a @ b / denominator)

    @staticmethod
    def similarity_matrix(rf_embeddings, unit_embeddings) -> np.ndarray:
        """matrix[i][j] = cosine(statement i, sentence j), as float32."""
        rf = Embedder.as_matrix(rf_embeddings)
        unit = Embedder.as_matrix(unit_embeddings)
        if rf.size == 0 or unit.size == 0:
            return np.zeros((len(rf), len(unit)), dtype=np.float32)
        if rf.shape[1] != unit.shape[1]:
            raise ValueError(f"Embedding dimensions mismatch: {rf.shape[1]} vs {unit.shape[1]}")
        rf_norm = rf / np.linalg.norm(rf, axis=1, keepdims=True).clip(min=1e-12)
        unit_norm = unit / np.linalg.norm(unit, axis=1, keepdims=True).clip(min=1e-12)
        return (rf_norm @ unit_norm.T).astype(np.float32)
