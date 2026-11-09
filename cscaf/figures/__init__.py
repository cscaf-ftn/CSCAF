"""The figures of the paper, one class per figure, all drawn in the style of `PaperStyle`.

Every figure is drawn from computed results passed by the notebook, never from numbers typed into the code: the
constructor takes the results and `draw(output)` writes the figure.
"""
from cscaf.figures.course_addition_figure import CourseAdditionFigure
from cscaf.figures.employer_pairs_figure import EmployerPairsFigure
from cscaf.figures.paper_style import PaperStyle
from cscaf.figures.programme_position_figure import ProgrammePositionFigure
from cscaf.figures.role_coverage_figure import RoleCoverageFigure
from cscaf.figures.role_demand_figure import RoleDemandFigure
from cscaf.figures.skills_against_knowledge_figure import SkillsAgainstKnowledgeFigure
from cscaf.figures.threshold_calibration_figure import ThresholdCalibrationFigure

__all__ = ["CourseAdditionFigure", "EmployerPairsFigure", "PaperStyle", "ProgrammePositionFigure",
           "RoleCoverageFigure", "RoleDemandFigure", "SkillsAgainstKnowledgeFigure", "ThresholdCalibrationFigure"]
