"""Figure 8 of the paper (Section 4.3): employer and curriculum pairs."""
from pathlib import Path

from cscaf.figures.paper_style import PaperStyle


class EmployerPairsFigure:
    """The coverage of the twelve roles by the curriculum of each employer set.

    Each panel: {"coverage": {role: C(r)}, "role": the role of the set, "declared": roles the programme declares in
    CyberHEAD, "title": the panel title}. `order` is the role order of every panel; `names` the ECSF role names.
    """

    def __init__(self, panels: list[dict], order: list[str], names: dict):
        self.panels = panels
        self.order = order
        self.names = names

    def draw(self, output: Path) -> Path:
        """Draw the figure and write it to `output`."""
        style, order = PaperStyle, self.order
        style.results()
        figure, axes = style.subplots(1, len(self.panels), figsize=(9.8, 3.8), sharey=True)
        for ax, panel in zip(axes, self.panels):
            values = [panel["coverage"][x] for x in order]
            colours = [style.ORANGE if x == panel["role"] else style.BAND for x in order]
            edges = [style.GREY if x in panel["declared"] else "none" for x in order]
            ax.barh(range(len(order)), values, color=colours, edgecolor=edges, linewidth=1.2)
            ax.set_xlim(0, 1)
            ax.set_xticks([0, 0.5, 1])
            ax.set_title(panel["title"], fontsize=8)
            ax.set_xlabel("coverage C(r)")
        axes[0].set_yticks(range(len(order)))
        axes[0].set_yticklabels([self.names[x].replace("Cybersecurity ", "").replace("Cyber ", "") for x in order],
                                fontsize=7)
        figure.tight_layout()
        return style.save(figure, output)
