"""Section 3.1 of the paper against methodology/output/01_reference_framework.json."""
def rows(record):
    """(name, value printed in the paper, value of the record) for every number compared."""

    units, profiles, overlap = record["units"], record["profiles"], record["overlap"]

    paper = {
        "role_statement_pairs": (227, units["role_statement_pairs"]),
        "skill_pairs": (103, units["skill_pairs"]),
        "knowledge_pairs": (124, units["knowledge_pairs"]),
        "statements": (150, units["statements"]),
        "skill_statements": (83, units["skill_statements"]),
        "knowledge_statements": (67, units["knowledge_statements"]),
        "smallest_profile": (12, profiles["smallest_profile"]),
        "largest_profile": (27, profiles["largest_profile"]),
        "single_role_statements": (121, profiles["single_role_statements"]),
        "shared_statements": (29, profiles["shared_statements"]),
        "most_shared_statements": (["Cybersecurity-related certifications"], profiles["most_shared_statements"]),
        "most_shared_roles": (9, profiles["most_shared_roles"]),
        "mean_share_percent": (47, round(100 * overlap["mean_share"])),
        "lowest_role": ("CISO", overlap["lowest_role"]),
        "lowest_share_percent": (33, round(100 * overlap["lowest_share"])),
        "highest_role": ("Implementer", overlap["highest_role"]),
        "highest_share_percent": (61, round(100 * overlap["highest_share"])),
        "architect_statements": (25, overlap["architect_statements"]),
        "architect_shared": (11, overlap["architect_shared"]),
        "architect_with_risk_manager": (6, overlap["architect_with_risk_manager"]),
        "architect_with_ciso": (3, overlap["architect_with_ciso"]),
    }

    return [(name, printed, computed) for name, (printed, computed) in paper.items()]
