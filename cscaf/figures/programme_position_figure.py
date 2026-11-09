"""Figure 6 of the paper (Section 4.2): the position of a programme."""
import statistics
from pathlib import Path

from cscaf.figures.paper_style import PaperStyle


class ProgrammePositionFigure:
    """The coverage of every role by one curriculum within the range of the corpus.

    `spread` maps a role to the sorted C(r) values of all curricula, `mine` to the C(r) of the curriculum drawn,
    `names` to the ECSF role names; `target` is the target role and `label` the legend name of the curriculum.
    Rows: the weakest role on top.
    """

    def __init__(self, spread: dict, mine: dict, names: dict, target: str, label: str):
        self.spread = spread
        self.mine = mine
        self.names = names
        self.target = target
        self.label = label

    def draw(self, output: Path) -> Path:
        """Draw the figure and write it to `output`."""
        style, mine, names, label = PaperStyle, self.mine, self.names, self.label
        style.results()
        order = sorted(names, key=lambda r: mine[r])
        figure, axes = style.subplots(figsize=(7.2, 4.8))
        for y, role in enumerate(order):
            values = self.spread[role]
            axes.plot([values[0], values[-1]], [y, y], color=style.BAND, linewidth=6, solid_capstyle="round",
                      zorder=1)
            axes.scatter(values, [y] * len(values), s=7, color=style.GREY, alpha=0.45, zorder=2, linewidths=0)
            median = statistics.median(values)
            axes.plot([median, median], [y - 0.30, y + 0.30], color=style.BLUE, linewidth=1.8, zorder=3,
                      label="median of the 27" if y == 0 else None)
            axes.scatter([mine[role]], [y], marker="o", s=56, color=style.ORANGE, zorder=4,
                         edgecolors="white", linewidths=0.8, label=label if y == 0 else None)
        axes.set_yticks(range(len(order)))
        axes.set_yticklabels([names[r] + ("   (target)" if r == self.target else "") for r in order])
        axes.invert_yaxis()
        axes.set_xlim(-0.02, 1.02)
        axes.set_xlabel("coverage of the role, $C(r)$")
        axes.set_ylim(len(order) - 0.4, -0.8)
        axes.grid(axis="y", visible=False)
        axes.plot([], [], color=style.BAND, linewidth=6, solid_capstyle="round", label="range across the 27")
        axes.scatter([], [], s=7, color=style.GREY, alpha=0.6, linewidths=0, label="one programme")
        handles, labels = axes.get_legend_handles_labels()
        wanted = ["range across the 27", "one programme", "median of the 27", label]
        pairs = dict(zip(labels, handles))
        axes.legend([pairs[name] for name in wanted if name in pairs], [name for name in wanted if name in pairs],
                    loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=4, frameon=False, fontsize=9,
                    handletextpad=0.4, columnspacing=1.6)
        figure.tight_layout()
        return style.save(figure, output, tight=True)
