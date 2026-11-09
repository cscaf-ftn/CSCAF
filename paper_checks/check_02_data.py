"""Section 3.2 and Table S1 of the paper against methodology/output/02_data.json."""
PAPER_S1 = {
    "Austria": ("2026/27", 16), "Belgium": ("2026/27", 21), "Bulgaria": ("2026/27", 15), "Croatia": ("2026/27", 23),
    "Cyprus": ("2026/27", 8), "Czechia": ("2026/27", 12), "Denmark": ("2026/27", 17), "Estonia": ("2025/26", 28),
    "Finland": ("2025/26", 7), "France": ("2025/26", 11), "Germany": ("2025/26", 20), "Greece": ("2026/27", 12),
    "Hungary": ("2024/25", 16), "Ireland": ("2026/27", 17), "Italy": ("2026/27", 14), "Latvia": ("2026/27", 16),
    "Lithuania": ("2026/27", 13), "Luxembourg": ("2025/26", 15), "Malta": ("2025/26", 5), "Netherlands": ("2026/27", 7),
    "Poland": ("2026/27", 26), "Portugal": ("2025/26", 9), "Romania": ("2026/27", 15), "Slovakia": ("2025/26", 28),
    "Slovenia": ("2026/27", 19), "Spain": ("2025/26", 12), "Sweden": ("2026/27", 19),
}


def rows(record):
    """(name, value printed in the paper, value of the record) for every number compared."""

    table_1, table_s1 = record["table_1"], record["table_s1"]
    curricula, advertisements, trainings = table_1["curricula"], table_1["advertisements"], table_1["trainings"]
    repeated, cyberhead, sans = record["repeated_descriptions"], record["cyberhead"], record["sans_selection"]

    c, a, t = curricula, advertisements, trainings
    paper = [
        ("Table 1 curricula", "27", str(c["curricula"])),
        ("Table 1 member states", "27", str(c["countries"])),
        ("Table 1 courses", "421", str(c["courses"])),
        ("Table 1 most common edition", "2026/27", c["most_common_edition"]),
        ("Table 1 advertisements", "5136", str(a["advertisements"])),
        ("Table 1 companies", "2118", str(a["companies"])),
        ("advertisement countries", "27", str(a["countries"])),
        ("Table 1 advertisements posted", "March 2025 - September 2026", a["period"]),
        ("Table 1 training courses", "22", str(t["courses"])),
        ("Table 1 training period", "October 2026", t["period"]),
        ("Table 1 sentences, curricula", "6910", str(c["sentences"])),
        ("Table 1 sentences, advertisements", "215747", str(a["sentences"])),
        ("Table 1 sentences, training courses", "789", str(t["sentences_primary"])),
        ("advertisements without a sentence", "0", str(a["without_sentence"])),
        ("same description as another of the company", "1669", str(repeated["advertisements"])),
        ("same description, share", "32.5%", f"{100 * repeated['share']:.1f}%"),
        ("programmes in CyberHEAD", "20", str(cyberhead["programmes_in_cyberhead"])),
        ("SANS: course of the rule for the CISO", "LDR551", sans["rule_first_for_ciso"]),
        ("SANS: course taken after LDR551 was set aside", "LDR521", sans["ciso_after_exclusion"]),
        ("SANS: courses in the corpus", "22", str(sans["courses"])),
    ]
    for row in table_s1:
        edition, courses_printed = PAPER_S1[row["country"]]
        paper.append((f"Table S1 {row['country']}: edition, courses", f"{edition}, {courses_printed}",
                      f"{row['edition']}, {row['courses']}"))

    return paper
