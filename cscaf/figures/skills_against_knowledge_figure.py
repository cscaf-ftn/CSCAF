"""Figure 5 of the paper (Section 4.1): skills against knowledge."""
from pathlib import Path

from cscaf.figures.paper_style import PaperStyle


class SkillsAgainstKnowledgeFigure:
    """The share of the skill statements against the share of the knowledge statements covered, one point per
    curriculum (`per_curriculum`: {"skills", "knowledge"} in the order of the curricula)."""

    def __init__(self, per_curriculum: list[dict], n_skills: int, n_knowledge: int):
        self.per_curriculum = per_curriculum
        self.n_skills = n_skills
        self.n_knowledge = n_knowledge

    def draw(self, output: Path) -> Path:
        """Draw the figure and write it to `output`."""
        style, per_curriculum = PaperStyle, self.per_curriculum
        style.results()
        above = sum(1 for v in per_curriculum if v["knowledge"] > v["skills"])
        figure, axes = style.subplots(figsize=(4.4, 4.4))
        axes.plot([0, 1], [0, 1], color=style.GREY, linewidth=1.0, linestyle="--", zorder=1)
        axes.scatter([v["skills"] for v in per_curriculum], [v["knowledge"] for v in per_curriculum],
                     s=38, color=style.BLUE, alpha=0.85, edgecolor="white", linewidth=0.8, zorder=3)
        axes.set_xlim(0, 1.0)
        axes.set_ylim(0, 1.0)
        axes.set_aspect("equal")
        axes.set_xlabel(f"share of the {self.n_skills} skill statements covered")
        axes.set_ylabel(f"share of the {self.n_knowledge} knowledge statements covered")
        axes.text(0.045, 0.955, f"{above} of {len(per_curriculum)} curricula\nlie above the diagonal",
                  fontsize=8, color=style.GREY, va="top")
        axes.text(0.62, 0.565, "equal coverage", fontsize=7.5, color=style.GREY, rotation=45, rotation_mode="anchor")
        figure.tight_layout()
        return style.save(figure, output)
