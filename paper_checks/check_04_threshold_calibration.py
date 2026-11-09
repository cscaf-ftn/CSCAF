"""Section 3.4 and Table S2 of the paper against methodology/output/04_threshold_calibration.json."""
def interval(values, digits=3):
    return f"[{values[0]:.{digits}f}, {values[1]:.{digits}f}]"


def fixed(value, digits=3):
    return f"{value:.{digits}f}"


def rows(record):
    """(name, value printed in the paper, value of the record) for every number compared."""

    results, agreement, sample = record, record["agreement"], record["sample"]
    settings, shares, table_s2 = record["settings"], record["shares"], record["table_s2"]
    s2 = table_s2
    curriculum, advertisement, both = s2["curriculum"], s2["job_advertisement"], s2["mean_of_sources"]
    overall = agreement["overall"]

    paper = [
        ("pairs", "300", str(sample["pairs"])),
        ("curriculum pairs", "150", str(sample["by_source"]["curriculum"])),
        ("advertisement pairs", "150", str(sample["by_source"]["job_advertisement"])),
        ("strata", "9", str(sample["strata"])),
        ("pairs in [0.45, 0.70)", "216", str(sample["transition_pairs"])),
        ("length groups", "3", str(sample["length_groups"])),
        ("pairs per statement at most", "3", str(sample["max_pairs_per_statement"])),
        ("statements", "132", str(sample["statements"])),
        ("pairs agreed", "279", str(round(overall["agreement"] * overall["n"]))),
        ("kappa", "0.854", fixed(overall["kappa"])),
        ("kappa interval", "[0.790, 0.911]", interval(overall["kappa_ci"])),
        ("kappa curricula", "0.834", fixed(agreement["curriculum"]["kappa"])),
        ("kappa advertisements", "0.875", fixed(agreement["job_advertisement"]["kappa"])),
        ("disagreements adjudicated", "21", str(record["adjudicated"])),
        ("bootstrap resamples", "5000", str(settings["bootstrap"])),
        ("tau", "0.585", fixed(results["tau"])),
        ("tau interval", "[0.580, 0.595]", interval(results["tau_ci"])),
        ("share matching below 0.60, at most", "0.27", fixed(shares["max_share_below_0_60"], 2)),
        ("share matching from 0.60, at least", "0.89", fixed(shares["min_share_from_0_60"], 2)),
        ("Fisher p, [0.39, tau) against below 0.39", "0.23", fixed(shares["partial_band_fisher_p"], 2)),
        ("ROC AUC", "0.938", fixed(results["sample_metrics"]["roc_auc"])),
        ("S2 curricula pairs (matching)", "150 (59)", f"{curriculum['pairs']} ({curriculum['matching']})"),
        ("S2 curricula TP/FP/FN/TN", "50/7/9/84", f"{curriculum['tp']}/{curriculum['fp']}/{curriculum['fn']}/{curriculum['tn']}"),
        ("S2 curricula precision", "0.876 [0.741, 0.972]", f"{fixed(curriculum['precision'])} {interval(curriculum['precision_ci'])}"),
        ("S2 curricula recall", "0.897 [0.819, 0.968]", f"{fixed(curriculum['recall'])} {interval(curriculum['recall_ci'])}"),
        ("S2 curricula specificity", "0.901 [0.809, 0.977]", f"{fixed(curriculum['specificity'])} {interval(curriculum['specificity_ci'])}"),
        ("S2 curricula F1", "0.887 [0.800, 0.947]", f"{fixed(curriculum['f1'])} {interval(curriculum['f1_ci'])}"),
        ("S2 advertisements pairs (matching)", "150 (58)", f"{advertisement['pairs']} ({advertisement['matching']})"),
        ("S2 advertisements TP/FP/FN/TN", "53/5/5/87", f"{advertisement['tp']}/{advertisement['fp']}/{advertisement['fn']}/{advertisement['tn']}"),
        ("S2 advertisements precision", "0.962 [0.919, 0.995]", f"{fixed(advertisement['precision'])} {interval(advertisement['precision_ci'])}"),
        ("S2 advertisements recall", "0.840 [0.660, 0.988]", f"{fixed(advertisement['recall'])} {interval(advertisement['recall_ci'])}"),
        ("S2 advertisements specificity", "0.994 [0.987, 0.999]", f"{fixed(advertisement['specificity'])} {interval(advertisement['specificity_ci'])}"),
        ("S2 advertisements F1", "0.897 [0.780, 0.980]", f"{fixed(advertisement['f1'])} {interval(advertisement['f1_ci'])}"),
        ("S2 mean pairs (matching)", "300 (117)", f"{both['pairs']} ({both['matching']})"),
        ("S2 mean TP/FP/FN/TN", "103/12/14/171", f"{both['tp']}/{both['fp']}/{both['fn']}/{both['tn']}"),
        ("S2 mean precision", "0.919 [0.850, 0.972]", f"{fixed(both['precision'])} {interval(both['precision_ci'])}"),
        ("S2 mean recall", "0.869 [0.771, 0.961]", f"{fixed(both['recall'])} {interval(both['recall_ci'])}"),
        ("S2 mean specificity", "0.947", fixed(both["specificity"])),
        ("S2 mean F1", "0.892 [0.821, 0.950]", f"{fixed(both['f1'])} {interval(both['f1_ci'])}"),
    ]

    return paper
