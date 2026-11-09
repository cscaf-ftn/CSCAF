"""Figure 2 of the paper (Section 3.4): the calibration of the matching threshold."""
import json
from pathlib import Path

import numpy as np

from cscaf.figures.paper_style import PaperStyle


class ThresholdCalibrationFigure:
    """The calibration of the matching rule in two panels: where tau lies, and why it lies there.

    (a) The objective (mean of the per-source population-weighted F1) against the candidate threshold, with tau
    and its bootstrap interval. (b) The share of annotated best-match pairs judged aligned in each similarity
    stratum (consensus labels, Wilson 95 % intervals), drawn over the stratum's score range, with tau marked.
    `results_file` is the JSON record of the calibration; `strata` are the stratum edges of `config.yaml`
    `threshold_validation.strata`.
    """

    def __init__(self, results_file: Path, strata: list[dict]):
        self.results = json.loads(Path(results_file).read_text(encoding="utf-8"))
        self.strata = strata

    def draw(self, output: Path, with_strata: bool = True) -> Path:
        """Draw the figure; with `with_strata=False` only panel (a) is drawn, untitled, as Figure 2 of the paper,
        which gives the strata in the text."""
        style = PaperStyle
        results = self.results
        grid = np.array(results["curve"]["grid"])
        values = np.array(results["curve"]["objective"])
        tau, (low, high) = results["tau"], results["tau_ci"]
        counts = {}
        for row in results["strata"]:
            n, positives = counts.get(row["stratum"], (0, 0))
            counts[row["stratum"]] = (n + row["n"], positives + row["positives"])

        style.methodology()
        if with_strata:
            figure, (left, right) = style.subplots(1, 2, figsize=(7.4, 3.2))
        else:
            figure, left = style.subplots(figsize=(5.0, 3.2))
        left.axvspan(low, high, color=style.LIGHT, alpha=0.8, label=f"95% bootstrap interval [{low:.3f}, {high:.3f}]")
        left.plot(grid, values, color=style.ACCENT, linewidth=1.6)
        left.axvline(tau, color=style.GREY, linestyle="--", linewidth=1.0, label=f"$\\tau$ = {tau:.3f}")
        left.set_xlabel("candidate threshold")
        left.set_ylabel("mean population-weighted F1")
        left.set_xlim(grid.min(), grid.max())
        if not with_strata:
            left.set_ylim(0, 1.0)
            left.legend(loc="upper left", frameon=False, fontsize=7)
            figure.tight_layout()
            return style.save(figure, output)
        left.set_title("(a) objective", fontsize=9, loc="left")
        left.legend(loc="upper right", frameon=False, fontsize=7)

        floor = 0.25
        for stratum in self.strata:
            n, positives = counts.get(stratum["h"], (0, 0))
            if not n:
                continue
            rate = positives / n
            z = 1.959964
            centre = (rate + z * z / (2 * n)) / (1 + z * z / n)
            half = z * np.sqrt(rate * (1 - rate) / n + z * z / (4 * n * n)) / (1 + z * z / n)
            x0, x1 = max(stratum["min"], floor), min(stratum["max"], 1.0)
            right.fill_between([x0, x1], [rate, rate], color=style.LIGHT, step="pre", alpha=0.9, linewidth=0)
            right.hlines(rate, x0, x1, color=style.ACCENT, linewidth=1.6)
            right.vlines((x0 + x1) / 2, max(centre - half, 0), min(centre + half, 1), color=style.GREY,
                         linewidth=1.0)
            right.text((x0 + x1) / 2, min(centre + half, 1) + 0.02, f"{positives}/{n}", ha="center", fontsize=6.5,
                       color=style.GREY)
        right.axvline(tau, color=style.GREY, linestyle="--", linewidth=1.0)
        right.set_xlim(floor, 1.0)
        right.set_ylim(0, 1.1)
        right.set_xlabel("similarity of the best match")
        right.set_ylabel("share judged aligned")
        right.set_title("(b) annotated pairs per stratum", fontsize=9, loc="left")
        return style.save(figure, output)
