"""The one style of the paper's figures: matplotlib, 600 dpi, the colours shared by every figure."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


class PaperStyle:
    """Sets the style before a figure is drawn, opens its axes and writes it at the paper's resolution."""

    DPI = 600
    FIGURE_SIZE = (6.0, 3.6)
    GREY, ACCENT, LIGHT = "#444444", "#1f4e79", "#c9d7e4"
    BLUE, ORANGE = "#2b74b8", "#d55e00"
    GREEN, BAND = "#009e73", "#c9d7e4"

    _COMMON = {"font.size": 9, "axes.grid": True, "grid.alpha": 0.3, "axes.spines.top": False,
               "axes.spines.right": False}

    @classmethod
    def methodology(cls) -> None:
        """The style of the Section 3 figures, laid out by matplotlib's automatic layout."""
        plt.rcParams.update({**cls._COMMON, "figure.autolayout": True})

    @classmethod
    def results(cls) -> None:
        """The style of the Section 4 figures, with the layout set by `tight_layout` alone."""
        plt.rcParams.update({**cls._COMMON, "figure.autolayout": False})

    @staticmethod
    def subplots(*args, **kwargs):
        """A new figure and its axes (`matplotlib.pyplot.subplots`), drawn in the style set before."""
        return plt.subplots(*args, **kwargs)

    @classmethod
    def save(cls, figure, output: Path, tight: bool = False) -> Path:
        """Write a figure at the paper's resolution and close it; `tight` crops it to its content (a legend below
        the axes)."""
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        if tight:
            figure.savefig(output, dpi=cls.DPI, bbox_inches="tight")
        else:
            figure.savefig(output, dpi=cls.DPI)
        plt.close(figure)
        return output
