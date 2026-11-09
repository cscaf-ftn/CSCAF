"""Figure 4 of the paper (Section 4.1): role demand with its interval."""
from pathlib import Path

import numpy as np

from cscaf.figures.paper_style import PaperStyle


class RoleDemandFigure:
    """B(r) with its 95 % bootstrap interval, least required role at the bottom.

    `demand` maps a role to {"binary_share", "ci_low", "ci_high"} as `AdvertisementDemand.role_interval`;
    `names` maps a role to its ECSF name.
    """

    def __init__(self, demand: dict, names: dict):
        self.demand = demand
        self.names = names

    def draw(self, output: Path) -> Path:
        """Draw the figure and write it to `output`."""
        style, demand = PaperStyle, self.demand
        style.results()
        by_demand = sorted(demand, key=lambda r: demand[r]["binary_share"])
        figure, axes = style.subplots(figsize=(6.4, 4.2))
        positions = np.arange(len(by_demand))
        point = [demand[r]["binary_share"] for r in by_demand]
        lower = [p - demand[r]["ci_low"] for p, r in zip(point, by_demand)]
        upper = [demand[r]["ci_high"] - p for p, r in zip(point, by_demand)]
        axes.errorbar(point, positions, xerr=[lower, upper], fmt="o", markersize=3.5, color=style.ORANGE,
                      ecolor=style.GREY, elinewidth=1.0, capsize=2.5, zorder=3)
        axes.set_yticks(positions)
        axes.set_yticklabels([self.names[r] for r in by_demand])
        axes.set_xlim(0, 0.30)
        axes.set_xlabel("B(r): mean share of advertisements per statement of the role", fontsize=8)
        axes.tick_params(labelsize=8)
        figure.tight_layout()
        return style.save(figure, output)
