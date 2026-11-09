"""The two sources of the annotated pairs (Section 3.4 of the paper)."""
from enum import StrEnum


class Source(StrEnum):
    """The source of a sentence: a curriculum or a job advertisement.

    The members are in the order of the analysis: the position of a member is the source index of the arrays of
    `ThresholdCalibration`, and every table lists the sources in this order.
    """

    CURRICULUM = "curriculum"
    JOB_ADVERTISEMENT = "job_advertisement"

    @classmethod
    def position(cls, value: str) -> int:
        """The index of a source in the order of the analysis."""
        return list(cls).index(cls(value))
