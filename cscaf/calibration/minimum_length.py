"""The minimum length of a unit, decided from the annotation by a rule fixed before labelling (Section 3.4).

The rule is in `config.yaml` `threshold_validation.minimum_length_rule`:

1. tau is estimated on all pairs (`ThresholdCalibration.analyze`);
2. among the pairs whose score reaches tau, the precision - the share labelled aligned - of units of exactly
   `short_words` words (2) is compared with that of units of `compare_from_words` words or more (3+);
3. if it is lower and a one-sided Fisher exact test gives p < `alpha`, the minimum unit length becomes
   `compare_from_words` words: shorter units are dropped from the segmentation and tau is estimated again
   on the remaining pairs;
4. otherwise the minimum stays at `short_words` words and tau stands.

The comparison uses the unweighted counts, as every Fisher test of the analysis does.

Re-estimating tau without the short units is an approximation, stated with the result: dropping them from
the segmentation would give some statements a different best match, which the labelled pairs cannot show.
The population count of a (stratum, source, length group) cell is reduced in proportion to the short
units among its sampled pairs, because `population.json` counts the cell, not each length in words.
"""
from scipy.stats import fisher_exact

from cscaf.calibration.threshold_calibration import ThresholdCalibration


class MinimumLength:
    """The minimum-length rule of `config.yaml` `threshold_validation.minimum_length_rule`."""

    def __init__(self, rule: dict):
        self.rule = rule

    def decide(self, pairs: list[dict], population: dict, settings: dict, seed: int) -> dict:
        """tau on all pairs, the comparison of short units, and tau again without them if the minimum rises.

        Returns {"comparison", "results_all", "results_final", "minimum_words"}; `results_final` is
        `results_all` when the minimum stays.
        """
        rule = self.rule
        results_all = ThresholdCalibration(pairs, population).analyze(settings, seed)
        comparison = self.compare_short_units(pairs, results_all["tau"])
        if comparison["minimum_words"] == rule["short_words"]:
            return {"comparison": comparison, "results_all": results_all, "results_final": results_all,
                    "minimum_words": rule["short_words"]}
        minimum = comparison["minimum_words"]
        kept = [p for p in pairs if self.words_of(p) >= minimum]
        population_kept = self._population_without_short(pairs, population, minimum)
        results_final = ThresholdCalibration(kept, population_kept).analyze(settings, seed)
        results_final["approximation"] = ("tau re-estimated on the labelled pairs without the short units; "
                                          "dropping them from the segmentation could change some best matches")
        return {"comparison": comparison, "results_all": results_all, "results_final": results_final,
                "minimum_words": minimum}

    def compare_short_units(self, pairs: list[dict], tau: float) -> dict:
        """Step 2 and 3 of the rule at a given tau: counts, precisions, the Fisher p and the decision."""
        rule = self.rule
        above = [p for p in pairs if p["similarity_score"] >= tau]
        short = [p for p in above if self.words_of(p) == rule["short_words"]]
        longer = [p for p in above if self.words_of(p) >= rule["compare_from_words"]]
        short_pos = sum(p["label_consensus"] for p in short)
        longer_pos = sum(p["label_consensus"] for p in longer)
        precision_short = short_pos / len(short) if short else None
        precision_longer = longer_pos / len(longer) if longer else None
        if short and longer:
            table = [[short_pos, len(short) - short_pos], [longer_pos, len(longer) - longer_pos]]
            p_value = float(fisher_exact(table, alternative="less")[1])
        else:
            p_value = 1.0
        lower = precision_short is not None and precision_longer is not None and precision_short < precision_longer
        raise_minimum = bool(lower and p_value < rule["alpha"])
        return {"tau": tau, "short_words": rule["short_words"], "compare_from_words": rule["compare_from_words"],
                "short_n": len(short), "short_aligned": short_pos, "precision_short": precision_short,
                "longer_n": len(longer), "longer_aligned": longer_pos, "precision_longer": precision_longer,
                "fisher_one_sided_p": p_value, "alpha": rule["alpha"],
                "minimum_words": rule["compare_from_words"] if raise_minimum else rule["short_words"],
                "decision": ("raise the minimum unit length" if raise_minimum else "keep the minimum unit length")}

    @staticmethod
    def words_of(pair: dict) -> int:
        """Words of the unit of a pair: stored by the sampler, counted from the sentence otherwise."""
        if pair.get("words") is not None:
            return pair["words"]
        if "sentence" in pair:
            return len(pair["sentence"].split())
        raise ValueError(f"pair {pair.get('pair_id')} has no word count: the minimum-length rule needs a sample "
                         f"drawn with length groups")

    @classmethod
    def _population_without_short(cls, pairs: list[dict], population: dict, minimum_words: int) -> dict:
        """population.json with each length-group cell reduced by the sampled share of units below the minimum."""
        cells = []
        for cell in population["cells"]:
            group = cell.get("length_group")
            inside = [p for p in pairs if p["stratum"] == cell["stratum"] and p["source"] == cell["source"]
                      and p.get("length_group") == group]
            kept = [p for p in inside if cls.words_of(p) >= minimum_words]
            share = len(kept) / len(inside) if inside else 1.0
            cells.append({**cell, "population": cell["population"] * share, "sampled": len(kept)})
        return {**population, "cells": cells}
