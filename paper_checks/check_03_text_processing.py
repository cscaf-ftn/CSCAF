"""Section 3.3 of the paper against methodology/output/03_text_processing.json."""
def rows(record):
    """(name, value printed in the paper, value of the record) for every number compared."""

    results = record["effect"]

    paper = [
        ("median curriculum, statements covered at 0.671", "27", str(results["published"]["curriculum_statements_median"])),
        ("median curriculum, statements covered at tau", "75", str(results["tau"]["curriculum_statements_median"])),
        ("advertisements requiring no statement at 0.671", "22.2%",
         f"{100 * results['published']['advertisements_without_statement_share']:.1f}%"),
        ("advertisements requiring no statement at tau", "2.8%",
         f"{100 * results['tau']['advertisements_without_statement_share']:.1f}%"),
    ]

    return paper
