"""The European Cybersecurity Skills Framework (ECSF) v1, from ENISA's machine-readable release.

Key skills and key knowledge only: 150 distinct statements (83 skills, 67 knowledge) in 227 role-statement rows.
The file is used unchanged; its SHA-256 and the expected counts are recorded in `config.yaml`
`reference_framework`, and any other file is refused: the statements are the base of every result.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cscaf.framework.reference_framework import ReferenceFramework


class ECSF(ReferenceFramework):
    """ECSF v1, read from the file of `config.yaml` `reference_framework.file`."""

    SHORT_NAMES = {
        "Chief Information Security Officer (CISO)": "CISO",
        "Cyber Incident Responder": "IncidentResponder",
        "Cyber Legal, Policy & Compliance Officer": "LegalCompliance",
        "Cyber Threat Intelligence Specialist": "ThreatIntel",
        "Cybersecurity Architect": "Architect",
        "Cybersecurity Auditor": "Auditor",
        "Cybersecurity Educator": "Educator",
        "Cybersecurity Implementer": "Implementer",
        "Cybersecurity Researcher": "Researcher",
        "Cybersecurity Risk Manager": "RiskManager",
        "Digital Forensics Investigator": "Forensics",
        "Penetration Tester": "PenTester",
    }

    def __init__(self, path: Path, settings: dict):
        self.path = Path(path)
        self.settings = settings

    @classmethod
    def of(cls, study) -> "ECSF":
        settings = study.section("reference_framework")
        return cls((study.root / settings["file"]).resolve(), settings)

    def short_name(self, title: str) -> str:
        return self.SHORT_NAMES[title]

    def _read(self) -> list[dict]:
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        if digest != self.settings["sha256"]:
            raise ValueError(f"{self.path.name} has SHA-256 {digest}, but config.yaml records {self.settings['sha256']}")
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _check(self, profiles: list[dict]) -> None:
        unknown = [p["title"] for p in profiles if p["title"] not in self.SHORT_NAMES]
        if unknown or len(profiles) != len(self.SHORT_NAMES):
            raise ValueError(f"the file does not hold the twelve expected profiles (unknown: {unknown})")
        rows = [s for p in profiles for _, field in self.SUBSECTIONS for s in p[field]]
        if len(rows) != self.settings["expected_rows"] or len(set(rows)) != self.settings["expected_statements"]:
            raise ValueError(f"{len(rows)} rows and {len(set(rows))} statements, expected "
                             f"{self.settings['expected_rows']} and {self.settings['expected_statements']}")
