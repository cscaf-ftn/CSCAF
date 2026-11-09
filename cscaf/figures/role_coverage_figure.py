"""Figure 3 of the paper (Section 4.1): role coverage across the curricula."""
import statistics
from pathlib import Path

import numpy as np

from cscaf.figures.paper_style import PaperStyle


class RoleCoverageFigure:
    """C(r) across the curricula, one box per role, least covered role at the bottom.

    `coverage` maps a role to its list of C(r) values, one per curriculum; `names` maps a role to its ECSF name.
    """

    def __init__(self, coverage: dict, names: dict):
        self.coverage = coverage
        self.names = names

    def draw(self, output: Path) -> Path:
        """Draw the figure and write it to `output`."""
        style, coverage = PaperStyle, self.coverage
        style.results()
        by_coverage = sorted(coverage, key=lambda r: statistics.median(coverage[r]))
        figure, axes = style.subplots(figsize=(6.4, 4.2))
        positions = np.arange(len(by_coverage))
        boxes = axes.boxplot([coverage[r] for r in by_coverage], positions=positions, vert=False, widths=0.62,
                             patch_artist=True, medianprops={"color": style.GREY, "linewidth": 1.2},
                             flierprops={"marker": ".", "markersize": 3, "markerfacecolor": style.GREY,
                                         "markeredgecolor": "none"},
                             whiskerprops={"color": style.GREY}, capprops={"color": style.GREY})
        for box in boxes["boxes"]:
            box.set(facecolor=style.BLUE, alpha=0.35, edgecolor=style.BLUE, linewidth=1.0)
        axes.set_yticks(positions)
        axes.set_yticklabels([self.names[r] for r in by_coverage])
        axes.set_xlim(0, 1.0)
        axes.set_xlabel("C(r): share of the role's statements covered by a curriculum", fontsize=8)
        axes.tick_params(labelsize=8)
        figure.tight_layout()
        return style.save(figure, output)
