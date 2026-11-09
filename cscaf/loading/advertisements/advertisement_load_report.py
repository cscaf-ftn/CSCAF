"""The report of an advertisement load."""
from __future__ import annotations

from dataclasses import dataclass, field

from cscaf.loading.load_report import LoadReport


@dataclass
class AdvertisementLoadReport(LoadReport):
    """What a load stored, checked against the database.

    `run_id` is None for step 1, which writes no sentences; the sentence checks then do not apply.
    """

    run_id: str | None = None
    started_at: str = field(default_factory=LoadReport.now)
    snapshot: dict = field(default_factory=dict)
    left_out: dict = field(default_factory=dict)
    ads_per_country: dict = field(default_factory=dict)
    date_range: dict = field(default_factory=dict)
    ads_segmented: int = 0
    sentences: int = 0
    sentences_by_part: dict = field(default_factory=lambda: {"title": 0, "description": 0})
    repeated: int = 0
    ads_without_sentences: list = field(default_factory=list)
    not_english: list = field(default_factory=list)

    def verify(self, storage) -> list[str]:
        problems = []
        ads_in_db = storage.count_rows("job_advertisement")
        if "n_loaded" in self.snapshot and ads_in_db != self.snapshot["n_loaded"]:
            problems.append(f"job_advertisement holds {ads_in_db} ads, the snapshot loaded {self.snapshot['n_loaded']}")
        if self.run_id is None:
            self.snapshot["ads_in_db"] = ads_in_db
            return problems
        sentences_in_db = storage.count_rows("job_advertisement_sentence", self.run_id)
        if self.ads_segmented and sentences_in_db < self.sentences:
            problems.append(f"{self.sentences} sentences stored in this session, the database holds {sentences_in_db}")
        missing = len(storage.advertisements.to_segment(self.run_id) or [])
        if missing:
            problems.append(f"{missing} ads have no sentences for run {self.run_id}")
        self.snapshot["ads_in_db"], self.snapshot["sentences_in_db"] = ads_in_db, sentences_in_db
        return problems

    def _stem(self) -> str:
        step = "load" if self.run_id is None else f"segmentation_{self.run_id}"
        return f"job_advertisement_{step}"

    def _content(self, problems: list[str], finished_at: str) -> dict:
        return {"run_id": self.run_id, "started_at": self.started_at, "finished_at": finished_at,
                "verified": not problems, "problems": problems, "snapshot": self.snapshot,
                "date_range": self.date_range, "ads_per_country": self.ads_per_country, "left_out": self.left_out,
                "segmentation": {"ads": self.ads_segmented, "sentences": self.sentences,
                                 "by_part": self.sentences_by_part, "repeated_within_an_ad": self.repeated,
                                 "ads_without_sentences": self.ads_without_sentences},
                "not_english": self.not_english}
