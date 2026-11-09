"""Figure 7 of the paper (Section 4.2): a course addition."""
from pathlib import Path

from cscaf.figures.paper_style import PaperStyle


class CourseAdditionFigure:
    """C(r) of every role before and after one course is added to a curriculum.

    `before` and `after` map a role to C(r); `ceilings` maps every other role to the most it can rise through the
    statements it shares with the `target` role; `names` maps a role to its ECSF name. Rows: the largest change
    on top.
    """

    def __init__(self, before: dict, after: dict, ceilings: dict, names: dict, target: str):
        self.before = before
        self.after = after
        self.ceilings = ceilings
        self.names = names
        self.target = target

    def draw(self, output: Path) -> Path:
        """Draw the figure and write it to `output`."""
        style, before, after, target = PaperStyle, self.before, self.after, self.target
        style.results()
        rows = sorted(self.names, key=lambda r: (-(after[r] - before[r]), r))
        figure, axes = style.subplots(figsize=(7.2, 5.0))
        for y, role in enumerate(rows):
            start, end = before[role], after[role]
            if role != target:
                reach = min(start + self.ceilings.get(role, 0.0), 1.0)
                axes.plot([start, reach], [y, y], color=style.BAND, linewidth=7, solid_capstyle="butt", zorder=1)
            if end > start:
                axes.annotate("", xy=(end, y), xytext=(start, y),
                              arrowprops=dict(arrowstyle="-|>", color=style.GREY, linewidth=0.9, shrinkA=0,
                                              shrinkB=2),
                              zorder=2)
            axes.plot([start, start], [y - 0.30, y + 0.30], color=style.BLUE, linewidth=1.8, zorder=3,
                      label="before" if y == 0 else None)
            axes.scatter([end], [y], marker="o", s=56, color=style.GREEN if role == target else style.ORANGE,
                         zorder=4, edgecolors="white", linewidths=0.8,
                         label=("after" if role != target else None) if y == 1 else None)
        axes.plot([], [], color=style.BAND, linewidth=7, solid_capstyle="butt",
                  label="reachable through the shared statements")
        axes.scatter([], [], marker="o", s=56, color=style.GREEN, edgecolors="white", linewidths=0.8,
                     label="after, target role")
        axes.set_yticks(range(len(rows)))
        axes.set_yticklabels([self.names[r] + ("   (target)" if r == target else "") for r in rows])
        axes.invert_yaxis()
        axes.set_xlim(-0.02, 1.02)
        axes.set_xlabel("coverage of the role, $C(r)$")
        axes.set_ylim(len(rows) - 0.4, -0.8)
        axes.grid(axis="y", visible=False)
        target_y = rows.index(target)
        axes.annotate(f"+{after[target] - before[target]:.3f}", xy=(after[target], target_y),
                      xytext=(after[target] + 0.03, target_y + 0.04), fontsize=8.5, color=style.GREEN, va="center")
        handles, labels = axes.get_legend_handles_labels()
        wanted = ["before", "after", "after, target role", "reachable through the shared statements"]
        pairs = dict(zip(labels, handles))
        axes.legend([pairs[name] for name in wanted if name in pairs], [name for name in wanted if name in pairs],
                    loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False, fontsize=9,
                    handletextpad=0.4, columnspacing=1.8)
        figure.tight_layout()
        return style.save(figure, output, tight=True)
