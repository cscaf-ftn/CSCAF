"""The weighting w(.) that turns a best-match similarity into coverage (Section 3.4 of the paper).

The bands are read from `config.yaml` and never written in the code. The weighting of the paper is binary: w = 1 at
or above tau, 0 below it. The bands are checked when they are read: they must cover the whole range of a cosine
similarity without a gap or an overlap, their weights must lie in [0, 1], a higher similarity must never receive a
smaller weight, and one band must start at tau.
"""
from __future__ import annotations

import numpy as np


class Bands:
    """A validated set of similarity bands and their weights, highest band first."""

    LOWEST, HIGHEST = -1.0, 1.01
    BINARY = "bands"

    def __init__(self, bands: list[dict], tau: float, key: str = BINARY):
        self.key = key
        self.tau = float(tau)
        self.bands = self._validated(bands, self.tau, key)

    @classmethod
    def of(cls, study, key: str = BINARY) -> "Bands":
        """The band set `key` of the study's configuration, with the study's tau."""
        if key not in study.config:
            raise ValueError(f"config.yaml has no band set named {key!r}")
        return cls(study.config[key], study.tau, key)

    @staticmethod
    def _validated(raw: list[dict], threshold: float, key: str) -> list[dict]:
        bands = sorted(({"min": float(b["min"]), "max": float(b["max"]), "w": float(b["w"])} for b in raw),
                       key=lambda b: b["min"], reverse=True)
        if not bands:
            raise ValueError(f"the band set {key!r} of config.yaml is empty")
        for band in bands:
            if not 0.0 <= band["w"] <= 1.0:
                raise ValueError(f"band {band} has a weight outside [0, 1]")
            if band["min"] >= band["max"]:
                raise ValueError(f"band {band} is empty")
        if bands[0]["max"] < Bands.HIGHEST or bands[-1]["min"] > Bands.LOWEST:
            raise ValueError(f"the bands do not cover [{Bands.LOWEST}, {Bands.HIGHEST}): {bands}")
        for higher, lower in zip(bands, bands[1:]):
            if higher["min"] != lower["max"]:
                raise ValueError(f"bands {lower} and {higher} leave a gap or overlap")
            if lower["w"] > higher["w"]:
                raise ValueError(f"band {lower} weighs more than the higher band {higher}")
        if not any(np.isclose(band["min"], threshold) for band in bands):
            raise ValueError(f"no band starts at tau = {threshold}: {bands}")
        return bands

    def weights(self, similarities: np.ndarray) -> np.ndarray:
        """w(similarity) for an array, in the same shape."""
        similarities = np.asarray(similarities, dtype=float)
        weights = np.zeros_like(similarities)
        assigned = np.zeros(similarities.shape, dtype=bool)
        for band in self.bands:
            inside = (similarities >= band["min"]) & (similarities < band["max"]) & ~assigned
            weights[inside] = band["w"]
            assigned |= inside
        if not assigned.all():
            raise ValueError(f"{int((~assigned).sum())} similarities fall outside every band, "
                             f"e.g. {similarities[~assigned][:3]}")
        return weights
