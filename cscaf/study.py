"""The study: every parameter of the paper, read once from `config.yaml`.

A `Study` is passed explicitly to every measure, so no value is read from a global state and no threshold is
written in the code. It holds the threshold tau of Section 3.4 and the ends of its 95 % interval, the seed, the 27
curricula of the analysis and the identifier of the run (the segmentation and embedding settings that produced the
stored similarities).
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import cached_property
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Study:
    """The configuration of the study and the values derived from it."""

    REPO_ROOT = Path(__file__).resolve().parents[1]
    CONFIG_FILE = REPO_ROOT / "config.yaml"
    DATABASE_FILE = REPO_ROOT / "database" / "CSCAF_public.db"
    SEGMENTATION_KEYS = ("engine", "version", "model", "model_revision", "tokenizer", "tokenizer_revision",
                         "half_precision", "split_on_input_newlines", "cleanup", "min_sentence_chars")
    EMBEDDING_KEYS = ("name", "revision", "precision", "embedding_dtype")

    config: dict = field(repr=False)
    root: Path = REPO_ROOT

    @classmethod
    def from_config(cls, path: Path | str | None = None) -> "Study":
        """The study described by `config.yaml` (or by the file at `path`)."""
        path = Path(path) if path else cls.CONFIG_FILE
        return cls(config=yaml.safe_load(path.read_text(encoding="utf-8")), root=path.resolve().parent)

    @property
    def tau(self) -> float:
        """The similarity at which a best match counts as covering a statement (Section 3.4)."""
        return float(self.config["threshold"]["tau"])

    @property
    def ends(self) -> tuple[float, ...]:
        """The ends of the 95 % interval of tau, at which every result acted on is repeated."""
        return tuple(float(value) for value in self.config["sensitivity"]["tau_appendix"])

    @property
    def seed(self) -> int:
        return int(self.config["seed"])

    @property
    def curricula(self) -> list[str]:
        """The keys of the 27 curricula of the analysis, in the order of `config.yaml`."""
        return list(self.config["sets"]["analysis_curricula"])

    @property
    def database_path(self) -> Path:
        return self.root / "database" / "CSCAF_public.db"

    @cached_property
    def run_id(self) -> str:
        """The run whose stored sentences and similarities the study reads."""
        return self.current_run(self.config)["run_id"]

    def run_record(self) -> dict:
        """The full record of the run, with the time it is created at."""
        return self.current_run(self.config)

    def section(self, name: str):
        """One section of `config.yaml`, e.g. `known_groups`."""
        return self.config[name]

    def at_tau(self, value: float) -> "Study":
        """The same study with tau moved to `value` and the binary weighting moved with it.

        Used for the ends of the interval of tau: every statement at or above `value` is covered, every one below
        is not.
        """
        moved = copy.deepcopy(self.config)
        moved["threshold"]["tau"] = value
        moved["bands"] = [{"min": value, "max": 1.01, "w": 1.0}, {"min": -1.0, "max": value, "w": 0.0}]
        return Study(config=moved, root=self.root)

    @staticmethod
    def _short(model_name: str) -> str:
        return model_name.split("/")[-1]

    @staticmethod
    def _code_version() -> str | None:
        try:
            return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=Study.REPO_ROOT, capture_output=True,
                                  text=True, check=True, timeout=10).stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            return None

    @staticmethod
    def current_run(config: dict) -> dict:
        """The run record of a configuration, ready for the `run` table."""
        segmentation, model = config["segmentation"], config["model"]
        fingerprint = {"segmentation": {key: segmentation.get(key) for key in Study.SEGMENTATION_KEYS},
                       "embedding": {key: model.get(key) for key in Study.EMBEDDING_KEYS}}
        if segmentation.get("preprocessing", {}).get("enabled", False):
            fingerprint["segmentation"]["preprocessing"] = segmentation["preprocessing"]
        config_hash = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode("utf-8")).hexdigest()
        return {
            "run_id": f"{Study._short(segmentation['model'])}_{Study._short(model['name'])}_{config_hash[:8]}",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "segmentation_engine": segmentation["engine"],
            "segmentation_model": segmentation["model"],
            "segmentation_revision": segmentation.get("model_revision"),
            "embedding_model": model["name"],
            "embedding_revision": model.get("revision"),
            "config_hash": config_hash,
            "code_version": Study._code_version(),
            "notes": None,
        }
