"""Section 4.1 and Table S3 of the paper against results/output/05_role_level_results.json."""
ROLE_NAMES = {"PenTester": "Penetration Tester", "CISO": "CISO", "IncidentResponder": "Incident Responder",
              "ThreatIntel": "Threat Intelligence Specialist", "Auditor": "Auditor", "RiskManager": "Risk Manager",
              "Architect": "Architect", "Forensics": "Digital Forensics Investigator",
              "LegalCompliance": "Legal, Policy & Compliance Officer"}
PAPER_ADVERTISEMENTS = {"PenTester": "229, 0.280 / 0.101, 1", "CISO": "136, 0.412 / 0.248, 1",
                        "IncidentResponder": "143, 0.348 / 0.179, 1", "ThreatIntel": "47, 0.315 / 0.102, 1",
                        "Auditor": "33, 0.360 / 0.157, 1", "RiskManager": "30, 0.333 / 0.178, 1",
                        "Architect": "87, 0.346 / 0.161, 2", "Forensics": "8 (not tested)"}
PAPER_CURRICULA = {"PenTester": "12 / 15, 0.507 / 0.475, 0.384", "IncidentResponder": "13 / 14, 0.688 / 0.500, 0.006",
                   "Auditor": "6 / 21, 0.510 / 0.289, 0.006", "RiskManager": "15 / 12, 0.629 / 0.521, 0.135",
                   "Architect": "4 / 23, 0.650 / 0.504, 0.153", "Forensics": "19 / 8, 0.640 / 0.493, 0.017",
                   "LegalCompliance": "13 / 14, 0.586 / 0.412, 0.051"}
PAPER_S3 = {
    "PenTester": ("penetration test; pentest; ethical hack; red team", "penetration; ethical hacking; offensive"),
    "CISO": ("ciso; chief information security", "-"),
    "IncidentResponder": ("incident respon; soc analyst; security operations cent; csirt", "incident; soc"),
    "ThreatIntel": ("threat intelligence; threat intel", "-"),
    "Auditor": ("auditor; audit", "audit"),
    "RiskManager": ("risk manager; risk management", "risk"),
    "Architect": ("security architect", "architect"),
    "Forensics": ("forensic", "forensic"),
    "LegalCompliance": ("-", "law; legal; regulation; compliance; gdpr"),
}


def fixed(value, digits=3):
    return f"{value:.{digits}f}"


def rows(record):
    """(name, value printed in the paper, value of the record) for every number compared."""

    TAU, ENDS, KEYS, DETECTION = record["tau"], record["ends"], record["curricula"], record["detection_level"]
    known_groups, roles, split = record["known_groups"], record["roles"], record["skills_against_knowledge"]
    rank_agreement, hubness, volume = record["rank_agreement"], record["hubness"], record["text_volume"]
    demand, keywords = {"n_ads": record["advertisements"]}, record["known_group_keywords"]
    communication = [entry["statement"] for entry in record["communication"]]
    untaught = [entry["statement"] for entry in record["untaught"]]
    shares = {entry["statement"]: entry["demand"] for entry in record["communication"] + record["untaught"]}
    taught_by = {entry["statement"]: entry["covered_by"] for entry in record["communication"]}
    text_of = {statement: statement for statement in communication}

    at = known_groups[f"{TAU:.3f}"]
    ads = {e["role"]: e for e in at["advertisements"]}
    cur = {e["role"]: e for e in at["curricula"]}
    tested_ads = [e for e in at["advertisements"] if e.get("enough")]
    tested_cur = [e for e in at["curricula"] if e.get("enough")]
    significant = [ROLE_NAMES[role] for role in ROLE_NAMES if role in cur and cur[role].get("enough") and cur[role]["p_value"] < 0.05]
    by_median = sorted(roles, key=lambda r: roles[r]["coverage_median"])
    by_demand = sorted(roles, key=lambda r: roles[r]["demand"])
    paper = []
    for role, printed in PAPER_ADVERTISEMENTS.items():
        e = ads[role]
        now = (f"{e['advertisements']}, {fixed(e['inside'])} / {fixed(e['outside'])}, {e['rank_of_role']}"
               if e.get("enough") else f"{e['advertisements']} (not tested)")
        paper.append((f"Table 3 advertisements {ROLE_NAMES[role]}", printed, now))
    for role, printed in PAPER_CURRICULA.items():
        e = cur[role]
        paper.append((f"Table 3 curricula {ROLE_NAMES[role]}", printed,
                      f"{e['with_course']} / {e['without_course']}, {fixed(e['inside'])} / {fixed(e['outside'])}, "
                      f"{fixed(e['p_value'])}"))
    paper += [
        ("advertisement groups, role higher inside", "7 of 7",
         f"{sum(1 for e in tested_ads if e['inside'] > e['outside'])} of {len(tested_ads)}"),
        ("advertisement groups, role first", "6 of 7",
         f"{sum(1 for e in tested_ads if e['rank_of_role'] == 1)} of {len(tested_ads)}"),
        ("the exception and the role before it", "Architect, CISO",
         ", ".join(f"{e['role']}, {e['strongest_role']}" for e in tested_ads if e["rank_of_role"] != 1)),
        ("curriculum groups, expected direction", "7 of 7",
         f"{sum(1 for e in tested_cur if e['inside'] > e['outside'])} of {len(tested_cur)}"),
        ("curriculum groups, p below 0.05", "Incident Responder, Auditor, Digital Forensics Investigator",
         ", ".join(significant)),
        ("pass condition at tau, 0.580, 0.595", "pass, pass, pass",
         ", ".join("pass" if known_groups[f"{t:.3f}"]["summary"]["passes"] else "fail" for t in [TAU] + ENDS)),
        ("Holm, significant at tau and at 0.580", "2, 1",
         f"{at['curriculum_significant_holm']}, {known_groups[f'{ENDS[0]:.3f}']['curriculum_significant_holm']}"),
        ("smallest range of C(r) over the roles", "0.556", fixed(min(v["coverage_range"] for v in roles.values()))),
        ("highest median C(r)", "CISO 0.704", f"{by_median[-1]} {fixed(roles[by_median[-1]]['coverage_median'])}"),
        ("lowest median C(r)", "Auditor 0.312", f"{by_median[0]} {fixed(roles[by_median[0]]['coverage_median'])}"),
        ("advertisements", "5136", str(demand["n_ads"])),
        ("highest B(r)", "CISO 0.252", f"{by_demand[-1]} {fixed(roles[by_demand[-1]]['demand'])}"),
        ("lowest B(r)", "Forensics 0.077", f"{by_demand[0]} {fixed(roles[by_demand[0]]['demand'])}"),
        ("second B(r)", "Educator 0.205", f"{by_demand[-2]} {fixed(roles[by_demand[-2]]['demand'])}"),
        ("median curriculum, skill statements covered", "0.482 of 83",
         f"{fixed(split['skills_median'])} of {split['skills']}"),
        ("median curriculum, knowledge statements covered", "0.567 of 67",
         f"{fixed(split['knowledge_median'])} of {split['knowledge']}"),
        ("curricula with the larger share in knowledge", "24 of 27", f"{split['knowledge_higher']} of {len(KEYS)}"),
        ("mean B(s), skills and knowledge", "0.163, 0.117",
         f"{fixed(split['demand_skills'])}, {fixed(split['demand_knowledge'])}"),
        ("Spearman of B(s) with curricula covering s", "0.746", fixed(rank_agreement["rho"])),
        ("statements with B(s) >= 0.20 covered by <= 6", "2", str(len(communication))),
        ("Communicate, present and report to relevant stakeholders", "0.242, 6",
         next(f"{fixed(shares[s])}, {taught_by[s]}" for s in communication
              if text_of[s] == "Communicate, present and report to relevant stakeholders")),
        ("Communicate, coordinate and cooperate with internal and external stakeholders", "0.213, 3",
         next(f"{fixed(shares[s])}, {taught_by[s]}" for s in communication
              if text_of[s] == "Communicate, coordinate and cooperate with internal and external stakeholders")),
        ("statements covered by no curriculum", "5", str(len(untaught))),
        ("their highest B(s)", "0.0062", fixed(max(shares[s] for s in untaught), 4)),
        ("false detection rate (1 - specificity)", "0.006", fixed(DETECTION)),
        ("Spearman, coverage without hub-only decisions", "0.957", fixed(hubness["spearman"])),
        ("Spearman, statements covered against sentences", "0.632, p < 0.001",
         f"{fixed(volume['sentences_rho'])}, " + ("p < 0.001" if volume["sentences_p"] < 0.001
                                                  else f"p = {fixed(volume['sentences_p'])}")),
        ("Spearman, statements covered against courses", "0.370, p = 0.057",
         f"{fixed(volume['courses_rho'])}, p = {fixed(volume['courses_p'])}"),
    ]
    for role, (printed_titles, printed_courses) in PAPER_S3.items():
        titles_now = "; ".join(k.strip() for k in keywords["advertisement_titles"].get(role, [])) or "-"
        courses_now = "; ".join(k.strip() for k in keywords["course_names"].get(role, [])) or "-"
        paper.append((f"Table S3 {ROLE_NAMES[role]}", f"{printed_titles} | {printed_courses}",
                      f"{titles_now} | {courses_now}"))

    return paper
