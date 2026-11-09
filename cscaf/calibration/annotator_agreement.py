"""Agreement between the two annotators (Section 3.4.1 of the paper): Cohen's kappa and raw agreement.

Both are reported overall and per source, each with a percentile bootstrap confidence interval (pairs
resampled with replacement, seeded). The quality gate applies to the overall kappa: below
`threshold_validation.analysis.kappa_gate` of `config.yaml` the annotation fails.
"""
import numpy as np

from cscaf.calibration.source import Source


class AnnotatorAgreement:
    """Cohen's kappa and raw agreement of the two annotators."""

    @staticmethod
    def kappa(a: np.ndarray, b: np.ndarray) -> float:
        """Cohen's kappa of two binary label vectors; 1.0 when both raters use one identical label throughout."""
        a, b = np.asarray(a, dtype=int), np.asarray(b, dtype=int)
        observed = float(np.mean(a == b))
        p_a, p_b = float(np.mean(a)), float(np.mean(b))
        expected = p_a * p_b + (1 - p_a) * (1 - p_b)
        if expected == 1.0:
            return 1.0 if observed == 1.0 else 0.0
        return (observed - expected) / (1 - expected)

    @classmethod
    def report(cls, pairs: list[dict], replicates: int, confidence: float, seed: int, kappa_gate: float) -> dict:
        """Kappa and agreement overall and per source, and whether the quality gate is passed."""
        report = {}
        groups = {"overall": pairs,
                  **{source.value: [p for p in pairs if p["source"] == source] for source in Source}}
        for name, group in groups.items():
            if not group:
                continue
            a = np.array([p["label_annotator_1"] for p in group])
            b = np.array([p["label_annotator_2"] for p in group])
            report[name] = cls._with_interval(a, b, replicates, confidence, seed)
        report["kappa_gate"] = kappa_gate
        report["gate_passed"] = report["overall"]["kappa"] >= kappa_gate
        return report

    @classmethod
    def _with_interval(cls, a: np.ndarray, b: np.ndarray, replicates: int, confidence: float, seed: int) -> dict:
        """Kappa and agreement of one group with their bootstrap intervals."""
        rng = np.random.default_rng(seed)
        n = len(a)
        kappas, agreements = [], []
        for _ in range(replicates):
            index = rng.integers(0, n, n)
            kappas.append(cls.kappa(a[index], b[index]))
            agreements.append(float(np.mean(a[index] == b[index])))
        low, high = (1 - confidence) / 2 * 100, (1 + confidence) / 2 * 100
        return {"n": n, "kappa": cls.kappa(a, b),
                "kappa_ci": [float(np.percentile(kappas, low)), float(np.percentile(kappas, high))],
                "agreement": float(np.mean(a == b)),
                "agreement_ci": [float(np.percentile(agreements, low)), float(np.percentile(agreements, high))],
                "positives_annotator_1": int(a.sum()), "positives_annotator_2": int(b.sum())}
