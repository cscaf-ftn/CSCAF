"""Section 4.2 of the paper against results/output/06_curriculum_update.json."""
from types import SimpleNamespace


class _Change:
    """The change of one course addition, as the record holds it."""

    def __init__(self, delta, sentences_added=0, crossed=0):
        self.delta = delta
        self.sentences_added = sentences_added
        self.crossed = crossed

    def delta_for(self, role):
        return self.delta


SHORT = {"PenTester": "Penetration Tester", "CISO": "CISO", "IncidentResponder": "Incident Responder",
         "ThreatIntel": "Threat Intelligence Specialist", "Auditor": "Auditor", "RiskManager": "Risk Manager",
         "Architect": "Architect", "Forensics": "Digital Forensics Investigator", "Implementer": "Implementer",
         "Educator": "Educator", "Researcher": "Researcher", "LegalCompliance": "Legal, Policy & Compliance Officer"}
PAPER_TABLE_4 = [
    ("Conduct ethical hacking", "skill", "0.518", "0.067",
     "to provide an understanding of types and methods of cybercrime, basic principles of investigation, and electronic evidence.",
     "Cybersecurity investigations"),
    ("Develop codes, scripts and programmes", "skill", "0.490", "0.095",
     "to develop practical skills in project development and management", "Project, change and professional management"),
    ("Computer systems vulnerabilities", "knowledge", "0.530", "0.055",
     "Can identify cybersecurity risks and assess their impact.", "CSX Cybersecurity fundamentals"),
    ("Information technology (IT) and operational technology (OT) appliances", "knowledge", "0.522", "0.063",
     "This course serves as basis to provide theoretical background for the top management of the company in the ICT field,",
     "ICT strategic governance"),
]
PAPER_TABLE_5 = [
    ("SEC542 Web App Penetration Testing and Ethical Hacking", "Penetration Tester", "52", "+0.217", "-"),
    ("SEC560 Enterprise Penetration Testing", "Penetration Tester", "41", "+0.174", "-"),
    ("SEC588 Cloud Penetration Testing", "Penetration Tester", "28", "+0.130", "-"),
    ("SEC565 Red Team Operations and Adversary Emulation", "Penetration Tester", "32", "+0.087", "-"),
    ("SEC555 Detection Engineering and SIEM Analytics", "Penetration Tester", "31", "0.000", "-"),
    ("SEC503 Network Monitoring and Threat Detection In-Depth", "Threat Intelligence Specialist", "38", "+0.043", "0.304"),
    ("FOR518 Mac and iOS Forensic Analysis and Incident Response", "Incident Responder", "24", "0.000", "0.261"),
    ("SEC501 Applied Cyber Defense", "Implementer", "36", "0.000", "0.261"),
    ("FOR498 Digital Acquisition and Rapid Triage", "Digital Forensics Investigator", "56", "0.000", "0.217"),
    ("LDR521 Security Culture for Leaders", "CISO", "27", "0.000", "0.130"),
    ("SEC403 Secrets to Successful Cybersecurity Presentations", "Educator", "22", "0.000", "0.130"),
    ("SEC497 Practical Open-Source Intelligence (OSINT)", "Researcher", "42", "+0.043", "0.130"),
    ("SEC530 Defensible Security Architecture and Engineering", "Architect", "22", "0.000", "0.130"),
]


EDITORIAL = {"Project, Change and professional management": "Project, change and professional management"}


def fixed(value, digits=3):
    return f"{value:.{digits}f}"


def signed(value):
    return "0.000" if abs(value) < 5e-4 else f"{value:+.3f}"


def shown(sentence):
    return sentence.strip("\u201c\u201d\" ").replace("\u2026", "").strip(" ,")


def rows(record):
    """(name, value printed in the paper, value of the record) for every number compared."""

    TARGET, TARGETS, CONTROLS = record["target_role"], record["target_courses"], record["controls"]
    FIGURE_COURSE, ENDS, additions = record["figure_course"], record["ends"], record["additions"]
    ORDER = list(additions)
    courses_of_curriculum, order, mine = record["courses"], record["role_order"], record["role_coverage"]
    dedicated, labels_against_content = record["roles_with_single_role_course"], record["course_labels_against_content"]
    newly_covered, target_uncovered = record["figure_course_newly_covered"], record["target_uncovered"]
    statements_of_role = target_uncovered["of"]
    recommendation = SimpleNamespace(statements=[SimpleNamespace(**s) for s in record["recommendation"]["statements"]])
    at_ends = {end: record["recommendation_at_ends"][str(end)] for end in ENDS}
    titles = {code: entry["title"] for code, entry in additions.items()}
    declared = {code: entry["declared"] for code, entry in additions.items()}
    unexplained = {code: entry["unexplained"] for code, entry in additions.items()}
    changes = {code: _Change(entry["delta"], entry["sentences"], entry["crossed"]) for code, entry in additions.items()}
    narrow = {code: _Change(entry["narrow"]) for code, entry in additions.items()}
    ends = {end: {code: entry["at_ends"][str(end)] for code, entry in additions.items()} for end in ENDS}

    def ceiling_for(code):
        return additions[code]["ceiling"]

    raised = [c for c in TARGETS if changes[c].delta_for(TARGET) > 1e-9]
    raised_deltas = [changes[c].delta_for(TARGET) for c in raised]
    control_deltas = [changes[c].delta_for(TARGET) for c in CONTROLS]
    step = 1 / statements_of_role
    paper = [
        ("courses of the curriculum", "16", str(courses_of_curriculum)),
        ("statements covered by the curriculum", "63", str(record["statements_covered"])),
        ("corpus median of statements covered", "75", f"{record['corpus_median']:g}"),
        ("strongest role", "CISO 0.778", f"{order[-1]} {fixed(mine[order[-1]])}"),
        ("weakest roles", "Auditor 0.250, PenTester 0.261",
         f"{order[0]} {fixed(mine[order[0]])}, {order[1]} {fixed(mine[order[1]])}"),
        ("Auditor has a single-role course", "no", "yes" if "Auditor" in dedicated else "no"),
        ("target role", "PenTester", TARGET),
        ("target statements uncovered (skills, knowledge)", "17 of 23 (9, 8)",
         f"{target_uncovered['statements']} of {statements_of_role} ({target_uncovered['skills']}, "
         f"{target_uncovered['knowledge']})"),
    ]
    for printed, s in zip(PAPER_TABLE_4, recommendation.statements):
        kind = s.subsection[:-1] if s.subsection.endswith("s") else s.subsection
        sentence_ok = shown(printed[4]) in (s.closest_sentence or "")
        paper.append((f"Table 4 {printed[0][:40]}", " | ".join(printed[:4] + (printed[5],)) + " | sentence",
                      " | ".join([s.statement, kind, fixed(s.similarity), fixed(s.distance_to_tau), EDITORIAL.get(s.closest_course, s.closest_course or "")])
                      + (" | sentence" if sentence_ok else f" | {s.closest_sentence}")))
    same_at_lower = [x[0] for x in at_ends[ENDS[0]]["statements"]] == [s.statement for s in recommendation.statements]
    upper = at_ends[ENDS[1]]
    upper_knowledge = [x for x in upper["statements"] if x[1] == "knowledge"]
    paper += [
        ("recommendation at 0.580", "the same", "the same" if same_at_lower else "different"),
        ("statements covered at 0.595", "5 of 23", f"{upper['covered']} of {statements_of_role}"),
        ("new knowledge statement at 0.595 and its best match", "Cybersecurity attack procedures, 0.593",
         ", ".join(f"{x[0]}, {fixed(x[2])}" for x in upper_knowledge
                   if x[0] not in [s.statement for s in recommendation.statements])),
        ("statement it replaces at 0.595", "Information technology (IT) and operational technology (OT) appliances",
         ", ".join(s.statement for s in recommendation.statements if s.subsection == "knowledge"
                   and s.statement not in [x[0] for x in upper["statements"]])),
        ("skills at 0.595 unchanged", "yes",
         "yes" if [x[0] for x in upper["statements"] if x[1] == "skills"] ==
         [s.statement for s in recommendation.statements if s.subsection == "skills"] else "no"),
        ("target courses, controls", "5, 8", f"{len(TARGETS)}, {len(CONTROLS)}"),
        ("courses: declared role best, another role, none", "11, 8, 3 of 22",
         ", ".join(str(len(v)) for v in labels_against_content.values()) + f" of {sum(len(v) for v in labels_against_content.values())}"),
    ]
    by_code = {row[0].split()[0]: row for row in PAPER_TABLE_5}
    for code in ORDER:
        printed = by_code[code]
        now = (f"{code} {titles[code]}", ", ".join(SHORT[r] for r in declared[code]), str(changes[code].sentences_added),
               signed(changes[code].delta_for(TARGET)), "-" if code in TARGETS else fixed(ceiling_for(code)))
        paper.append((f"Table 5 {code}", " | ".join(printed), " | ".join(now)))
    paper += [
        ("Table 5 order", ", ".join(by_code), ", ".join(sorted(TARGETS, key=lambda c: -changes[c].delta_for(TARGET)) + list(CONTROLS))),
        ("target courses that raise the role", "4 of 5", f"{len(raised)} of {len(TARGETS)}"),
        ("their range", "0.087 to 0.217", f"{fixed(min(raised_deltas))} to {fixed(max(raised_deltas))}"),
        ("in statements", "2 to 5", f"{round(min(raised_deltas) / step)} to {round(max(raised_deltas) / step)}"),
        ("course of Figure 7", "SEC542", FIGURE_COURSE),
        ("statements SEC542 adds", "5, Identify and exploit vulnerabilities among them",
         f"{len(newly_covered)}, " + ("Identify and exploit vulnerabilities among them"
                                      if "Identify and exploit vulnerabilities" in newly_covered else "missing")),
        ("target course that adds nothing", "SEC555", ", ".join(c for c in TARGETS if c not in raised)),
        ("controls unchanged, controls +0.043", "6, 2",
         f"{sum(1 for d in control_deltas if d < 1e-9)}, {sum(1 for d in control_deltas if abs(d - step) < 1e-9)}"),
        ("controls within their ceiling", "all",
         "all" if all(changes[c].delta_for(TARGET) <= ceiling_for(c) + 1e-9 for c in CONTROLS) else "not all"),
        ("side effects of target courses beyond the overlap", "none",
         ", ".join(f"{c}: {unexplained[c]}" for c in TARGETS if unexplained[c]) or "none"),
        ("at both ends: target courses raising the role", "4, 4",
         ", ".join(str(sum(1 for c in TARGETS if ends[v][c] > 1e-9)) for v in ENDS)),
        ("at both ends: largest control change, in statements", "1, 1",
         ", ".join(str(round(max(ends[v][c] for c in CONTROLS) / step)) for v in ENDS)),
        ("overview alone: range of the four", "0.087 to 0.174",
         f"{fixed(min(narrow[c].delta_for(TARGET) for c in raised))} to {fixed(max(narrow[c].delta_for(TARGET) for c in raised))}"),
        ("overview alone: controls at zero", "all",
         "all" if all(narrow[c].delta_for(TARGET) == 0.0 for c in CONTROLS) else "not all"),
        ("courses raising a recommended statement above tau", "0 of 13",
         f"{sum(1 for c in ORDER if changes[c].crossed)} of {len(ORDER)}"),
        ("Figure 7: other roles within their bar", "all",
         "all" if record["figure_course_other_roles_within_bar"] else "not all"),
    ]

    return paper
