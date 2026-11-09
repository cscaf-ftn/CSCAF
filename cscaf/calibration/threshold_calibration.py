"""The threshold tau and its interval from the consensus labels (Section 3.4.2 of the paper).

A pair in stratum h and source c weighs W = N_hc / n_hc, where N_hc is the population count of its cell
(`population.json` of the annotation) and n_hc the number of labelled pairs in that cell.

On the grid `threshold_validation.analysis.grid` of `config.yaml`, the objective at t is the mean over the two
sources of the population-weighted F1 of that source. tau maximises it; on a plateau, tau is the midpoint of the
longest run of maximal values, rounded to the grid step. Its confidence interval comes from a stratified bootstrap
that resamples pairs within each stratum x source cell. The value that balanced accuracy would give is reported
beside it and takes no part in selecting tau.

Metrics: at sample level (unweighted) the confusion matrix, precision, recall, F1, accuracy, ROC AUC and average
precision; population-weighted, precision, recall and F1 per source, their mean and the pooled value, each with a
bootstrap interval.

Bands: similarity >= tau has w = 1. The partial bands [0.39, 0.45) and [0.45, tau) are merged if a two-sided Fisher
test does not separate them, and a band is dropped (w = 0) if a one-sided Fisher test does not show its rate above
that of the pairs below 0.39; below 0.39, w = 0. Wilson intervals and the Fisher tests use the unweighted counts.
"""
import numpy as np
from scipy.stats import fisher_exact, norm
from sklearn.metrics import average_precision_score, roc_auc_score

from cscaf.calibration.source import Source


class ThresholdCalibration:
    """The calibration of tau on one annotated sample: the weighted pairs, the analysis and the bootstrap cells.

    The pairs are turned into arrays once, in the constructor (`data`): the score, the consensus label, the source
    index (the position in `Source`), the cell and the population weight of every pair.
    """

    LOWER_EDGE, MIDDLE_EDGE = 0.39, 0.45
    BOTTOM, TOP = -1.00, 1.01

    def __init__(self, pairs: list[dict], population: dict):
        if any(p["label_consensus"] is None for p in pairs):
            raise ValueError("every pair needs its consensus label before the analysis")
        self.pairs = pairs
        self.population = population
        population_of = {(c["stratum"], c["source"], c.get("length_group")): c["population"]
                         for c in population["cells"]}
        cells = [(p["stratum"], p["source"], p.get("length_group")) for p in pairs]
        sampled = {cell: cells.count(cell) for cell in set(cells)}
        self.data = {"score": np.array([p["similarity_score"] for p in pairs], dtype=float),
                     "label": np.array([p["label_consensus"] for p in pairs], dtype=int),
                     "source": np.array([Source.position(p["source"]) for p in pairs]),
                     "cell": cells,
                     "weight": np.array([population_of[cell] / sampled[cell] for cell in cells], dtype=float)}


    def analyze(self, settings: dict, seed: int) -> dict:
        """tau, its interval, the metrics, the strata and the bands."""
        grid_settings = settings["grid"]
        grid = np.round(np.arange(grid_settings["min"], grid_settings["max"] + grid_settings["step"] / 2,
                                  grid_settings["step"]), 6)
        values = self.objective(grid)
        tau = self.select_tau(grid, values, grid_settings["step"])
        balanced = self.balanced_accuracy_objective(grid)
        tau_balanced = self.select_tau(grid, balanced, grid_settings["step"])

        rng = np.random.default_rng(seed)
        cells = self.cell_indices()
        boot_tau, boot_metrics = [], []
        for _ in range(settings["bootstrap"]):
            index = np.concatenate([rng.choice(cell, size=len(cell), replace=True) for cell in cells])
            boot_tau.append(self.select_tau(grid, self.objective(grid, index), grid_settings["step"]))
            boot_metrics.append(self.weighted_metrics_at(tau, index))
        confidence = settings["confidence"]
        weighted = self.weighted_metrics_at(tau)
        for group, metrics in weighted.items():
            for name in ("precision", "recall", "f1"):
                metrics[f"{name}_ci"] = self._interval([m[group][name] for m in boot_metrics if group in m],
                                                       confidence)
        sources = [s.value for i, s in enumerate(Source) if np.any(self.data["source"] == i)]
        return {"n_pairs": len(self.pairs), "sources": sources,
                "tau": tau, "tau_ci": self._interval(boot_tau, confidence),
                "objective_at_tau": float(np.interp(tau, grid, values)),
                "tau_balanced_accuracy": tau_balanced,
                "balanced_accuracy_at_tau_balanced": float(np.interp(tau_balanced, grid, balanced)),
                "balanced_accuracy_at_tau": float(np.interp(tau, grid, balanced)),
                "curve": {"grid": grid.tolist(), "objective": values.tolist()},
                "sample_metrics": self.sample_metrics_at(tau), "weighted_metrics": weighted,
                "strata": self.strata_table(tau, confidence),
                "r3": self.bands_rule_r3(tau, settings), "settings": settings, "seed": seed}

    def cell_indices(self) -> list[np.ndarray]:
        """The indices of the pairs of each stratum x source cell, the unit of the stratified bootstrap."""
        cells = self.data["cell"]
        return [np.array([i for i, c in enumerate(cells) if c == cell]) for cell in sorted(set(cells))]


    def objective(self, grid: np.ndarray, index: np.ndarray | None = None) -> np.ndarray:
        """Mean over the sources present of the population-weighted F1, at every grid value."""
        score, label, source, weight = self._arrays(index)
        curves = [self.weighted_prf(score[source == s], label[source == s], weight[source == s], grid)[2]
                  for s in range(len(Source)) if np.any(source == s)]
        return np.mean(curves, axis=0)

    def balanced_accuracy_objective(self, grid: np.ndarray) -> np.ndarray:
        """Mean over the sources present of the population-weighted balanced accuracy.

        The companion of `objective`, built the same way; only the per-source measure differs.
        """
        score, label, source, weight = self._arrays()
        curves = [self.weighted_balanced_accuracy(score[source == s], label[source == s], weight[source == s], grid)
                  for s in range(len(Source)) if np.any(source == s)]
        return np.mean(curves, axis=0)

    @staticmethod
    def select_tau(grid: np.ndarray, values: np.ndarray, step: float) -> float:
        """The grid value maximising `values`; on a plateau, the midpoint of the longest maximal run."""
        best = values.max()
        maximal = np.flatnonzero(np.isclose(values, best, rtol=0, atol=1e-12))
        runs, start = [], maximal[0]
        for previous, current in zip(maximal, maximal[1:]):
            if current != previous + 1:
                runs.append((start, previous))
                start = current
        runs.append((start, maximal[-1]))
        first, last = max(runs, key=lambda run: run[1] - run[0])
        return round(round((grid[first] + grid[last]) / 2 / step) * step, 6)

    @classmethod
    def weighted_prf(cls, score, label, weight, thresholds):
        """Weighted precision, recall and F1 at every threshold (vectors over `thresholds`)."""
        above = score[None, :] >= np.asarray(thresholds)[:, None]
        positive = label[None, :] == 1
        tp = (weight * (above & positive)).sum(axis=1)
        fp = (weight * (above & ~positive)).sum(axis=1)
        fn = (weight * (~above & positive)).sum(axis=1)
        return cls._f1(tp, fp, fn)

    @staticmethod
    def weighted_balanced_accuracy(score, label, weight, thresholds):
        """Weighted balanced accuracy, (sensitivity + specificity) / 2, at every threshold."""
        above = score[None, :] >= np.asarray(thresholds)[:, None]
        positive = label[None, :] == 1
        tp = (weight * (above & positive)).sum(axis=1)
        fn = (weight * (~above & positive)).sum(axis=1)
        tn = (weight * (~above & ~positive)).sum(axis=1)
        fp = (weight * (above & ~positive)).sum(axis=1)
        sensitivity = np.divide(tp, tp + fn, out=np.zeros_like(tp, dtype=float), where=(tp + fn) > 0)
        specificity = np.divide(tn, tn + fp, out=np.zeros_like(tn, dtype=float), where=(tn + fp) > 0)
        return (sensitivity + specificity) / 2


    def weighted_metrics_at(self, tau: float, index: np.ndarray | None = None) -> dict:
        """Population-weighted precision, recall and F1 at tau: per source, their mean, and pooled."""
        score, label, source, weight = self._arrays(index)
        result = {}
        for s, name in enumerate(Source):
            mask = source == s
            if mask.any():
                p, r, f = self.weighted_prf(score[mask], label[mask], weight[mask], [tau])
                result[name.value] = {"precision": float(p[0]), "recall": float(r[0]), "f1": float(f[0])}
        present = [result[name.value] for name in Source if name.value in result]
        result["mean_of_sources"] = {k: float(np.mean([m[k] for m in present])) for k in ("precision", "recall", "f1")}
        p, r, f = self.weighted_prf(score, label, weight, [tau])
        result["pooled"] = {"precision": float(p[0]), "recall": float(r[0]), "f1": float(f[0])}
        return result

    def sample_metrics_at(self, tau: float) -> dict:
        """Unweighted confusion matrix and metrics of the stratified sample."""
        score, label = self.data["score"], self.data["label"]
        predicted = score >= tau
        tp, fp = int(np.sum(predicted & (label == 1))), int(np.sum(predicted & (label == 0)))
        fn, tn = int(np.sum(~predicted & (label == 1))), int(np.sum(~predicted & (label == 0)))
        precision, recall, f1 = (float(v[0]) for v in self._f1(np.array([tp]), np.array([fp]), np.array([fn])))
        both_classes = 0 < label.sum() < len(label)
        return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall, "f1": f1,
                "accuracy": (tp + tn) / len(label),
                "roc_auc": float(roc_auc_score(label, score)) if both_classes else None,
                "average_precision": float(average_precision_score(label, score)) if both_classes else None}

    def strata_table(self, tau: float, confidence: float) -> list[dict]:
        """Per stratum and source: pairs, positives, the match rate with its Wilson interval, and the
        confusion counts at tau. The match rate of a cell is the estimated probability that a best match
        in that score range expresses the statement."""
        data = self.data
        rows = []
        for stratum, source_name, group in sorted(set(data["cell"]), key=lambda c: (c[0], c[1], c[2] or "")):
            mask = np.array([cell == (stratum, source_name, group) for cell in data["cell"]])
            label, above = data["label"][mask], data["score"][mask] >= tau
            positives, n = int(label.sum()), int(mask.sum())
            rows.append({"stratum": stratum, "source": source_name, "length_group": group, "n": n,
                         "positives": positives, "rate": positives / n,
                         "wilson_ci": self._wilson(positives, n, confidence),
                         "population": float(data["weight"][mask][0] * n),
                         "tp": int(np.sum(above & (label == 1))), "fp": int(np.sum(above & (label == 0))),
                         "fn": int(np.sum(~above & (label == 1))), "tn": int(np.sum(~above & (label == 0)))})
        return rows

    @staticmethod
    def rates_by_stratum(strata_rows: list[dict]) -> dict:
        """{stratum: {"n", "positives", "rate"}} over every source and length group: the unweighted match rate of
        each stratum, the figure that can be compared between two validation rounds with the same strata."""
        totals = {}
        for row in strata_rows:
            cell = totals.setdefault(row["stratum"], {"n": 0, "positives": 0})
            cell["n"] += row["n"]
            cell["positives"] += row["positives"]
        return {h: {**c, "rate": c["positives"] / c["n"] if c["n"] else None} for h, c in sorted(totals.items())}


    def bands_rule_r3(self, tau: float, settings: dict) -> dict:
        """Band weights by the band rule of Section 3.4.2; returns the bands and every intermediate step."""
        method, alpha, step, confidence = (settings["band_rate"], settings["fisher_alpha"], settings["weight_step"],
                                           settings["confidence"])
        lower, middle, bottom, top_edge = self.LOWER_EDGE, self.MIDDLE_EDGE, self.BOTTOM, self.TOP
        steps = []
        reference = self._band(bottom, lower, method, confidence)
        if tau > middle:
            candidates = [self._band(lower, middle, method, confidence), self._band(middle, tau, method, confidence)]
            p_merge = self._fisher(candidates[0], candidates[1], "two-sided")
            steps.append({"test": "merge [0.39, 0.45) with [0.45, tau)", "p": p_merge})
            if p_merge >= alpha:
                candidates = [self._band(lower, tau, method, confidence)]
        elif tau > lower:
            candidates = [self._band(lower, tau, method, confidence)]
        else:
            candidates = []

        def weigh(band):
            p_drop = self._fisher(band, reference, "greater")
            steps.append({"test": f"drop [{band['min']}, {band['max']}) against the pairs below 0.39", "p": p_drop})
            w = round(round(band["rate"] / step) * step, 2) if p_drop < alpha else 0.0
            return {**band, "p_drop": p_drop, "w": w}

        weighted = [weigh(band) for band in candidates]
        if len(weighted) == 2 and weighted[0]["w"] > weighted[1]["w"]:
            steps.append({"test": "monotonicity: the lower band outweighs the upper one, merged", "p": None})
            weighted = [weigh(self._band(lower, tau, method, confidence))]
        top = self._band(tau, top_edge, method, confidence)
        bands = ([{"min": tau, "max": top_edge, "w": 1.0}]
                 + [{"min": b["min"], "max": b["max"], "w": b["w"]} for b in reversed(weighted)]
                 + [{"min": bottom, "max": lower if candidates else tau, "w": 0.0}])
        return {"bands": bands, "top": top, "partial": weighted, "reference_below_0_39": reference, "steps": steps}

    def _band(self, low: float, high: float, method: str, confidence: float) -> dict:
        """The pairs with a score in [low, high): counts, the match rate (per source and overall) and its interval."""
        score, label, source, weight = self._arrays()
        inside = (score >= low) & (score < high)
        rates = {}
        for s, name in enumerate(Source):
            mask = inside & (source == s)
            if mask.any():
                rates[name.value] = float(weight[mask & (label == 1)].sum() / weight[mask].sum())
        if method == "pooled":
            rate = float(weight[inside & (label == 1)].sum() / weight[inside].sum()) if inside.any() else 0.0
        else:
            rate = float(np.mean(list(rates.values()))) if rates else 0.0
        positives, n = int(np.sum(inside & (label == 1))), int(inside.sum())
        return {"min": low, "max": high, "n": n, "positives": positives, "rate": rate, "rate_per_source": rates,
                "wilson_ci": self._wilson(positives, n, confidence)}


    def _arrays(self, index: np.ndarray | None = None) -> tuple:
        """Score, label, source index and weight of the pairs in `index` (every pair when None)."""
        index = np.arange(len(self.data["score"])) if index is None else index
        return tuple(self.data[k][index] for k in ("score", "label", "source", "weight"))

    @staticmethod
    def _f1(tp, fp, fn):
        precision = np.divide(tp, tp + fp, out=np.zeros_like(tp, dtype=float), where=(tp + fp) > 0)
        recall = np.divide(tp, tp + fn, out=np.zeros_like(tp, dtype=float), where=(tp + fn) > 0)
        f1 = np.divide(2 * precision * recall, precision + recall, out=np.zeros_like(tp, dtype=float),
                       where=(precision + recall) > 0)
        return precision, recall, f1

    @staticmethod
    def _interval(values, confidence):
        low, high = (1 - confidence) / 2 * 100, (1 + confidence) / 2 * 100
        return [float(np.percentile(values, low)), float(np.percentile(values, high))]

    @staticmethod
    def _wilson(positives: int, n: int, confidence: float) -> list[float] | None:
        if n == 0:
            return None
        z = norm.ppf((1 + confidence) / 2)
        p = positives / n
        centre = (p + z * z / (2 * n)) / (1 + z * z / n)
        half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
        return [float(centre - half), float(centre + half)]

    @staticmethod
    def _fisher(band_a: dict, band_b: dict, alternative: str) -> float:
        table = [[band_a["positives"], band_a["n"] - band_a["positives"]],
                 [band_b["positives"], band_b["n"] - band_b["positives"]]]
        if band_a["n"] == 0 or band_b["n"] == 0:
            return 1.0
        return float(fisher_exact(table, alternative=alternative)[1])
