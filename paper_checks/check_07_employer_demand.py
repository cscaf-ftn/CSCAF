"""Section 4.3, Table 7 and Table S4 of the paper against results/output/07_employer_demand.json."""
S4_ROLE = {"ThreatIntel": "Threat Intelligence", "Forensics": "Forensics", "LegalCompliance": "Legal, Policy & Compliance",
           "CISO": "CISO", "Educator": "Educator", "Auditor": "Auditor", "RiskManager": "Risk Manager",
           "PenTester": "Penetration Tester", "Researcher": "Researcher", "Implementer": "Implementer",
           "IncidentResponder": "Incident Responder", "Architect": "Architect"}
S4_UNIVERSITY = {"be_kuleuven": "KU Leuven", "dk_aau": "Aalborg University", "fi_jamk": "JAMK University of Applied Sciences",
                 "fr_ubs": "Université Bretagne Sud", "gr_ihu": "International Hellenic University",
                 "hu_nke": "Ludovika University of Public Service", "ie_mtu": "Munster Technological University",
                 "it_unipi": "University of Pisa", "lv_lu": "University of Latvia", "mt_um": "University of Malta",
                 "pl_prz": "Rzeszów University of Technology", "pt_ipleiria": "Polytechnic of Leiria",
                 "ro_utcn": "Technical University of Cluj-Napoca", "sk_tuke": "Technical University of Košice",
                 "si_fis": "University of Novo Mesto", "es_uah": "University of Alcalá",
                 "se_kth": "KTH Royal Institute of Technology"}
PAPER_S4 = """Belgium | BE-1 (32)¹ | international organisation | KU Leuven | Threat Intelligence (L) | no | 0.348 (11) | 0.573 | 4 (2) | mission
Belgium | BE-2 (12) | agency | KU Leuven | Threat Intelligence (L) | no | 0.348 (11) | 0.443 | 4 (2) | mission
Belgium | BE-3 (12) | employer | KU Leuven | Forensics (L) | no | 0.444 (9) | 0.460 | 4 (4) | mission
Denmark | DK-1 (12) | employer | Aalborg University | Legal, Policy & Compliance (L) | no | 0.846 (2) | 0.038 | 0 | no gap
Finland | FI-1 (10) | employer | JAMK University of Applied Sciences | Forensics (L) | no | 0.500 (9) | 0.043 | 0 | no gap
France | FR-1 (10) | employer | Université Bretagne Sud | Forensics (L) | no | 0.278 (6) | 0.714 | 5 (4) | mission
France | FR-2 (10) | employer | Université Bretagne Sud | CISO (T) | no | 0.333 (4) | 0.537 | 9 (5) | mission
Greece | GR-1 (11) | employer | International Hellenic University | Legal, Policy & Compliance (L) | no | 0.615 (7) | 0.333 | 2 (1) | mission
Hungary | HU-1 (40) | job board | Ludovika University of Public Service | Educator (L) | no | 0.882 (5) | 0.000 | – | no message (no role preference)
Hungary | HU-2 (20) | agency (RPO) | Ludovika University of Public Service | Auditor (L) | no | 0.500 (12) | 0.339 | 3 (3) | mission
Ireland | IE-1 (11) | agency | Munster Technological University | Risk Manager (L) | no | 0.562 (7) | 0.290 | 4 (3) | mission
Ireland | IE-2 (10) | employer | Munster Technological University | Penetration Tester (T) | yes | 0.609 (6) | 0.107 | 1 (1) | confirm
Italy | IT-1 (12) | employer | University of Pisa | Researcher (L) | yes | 0.417 (9) | 0.475 | 3 (1) | confirm
Latvia | LV-1 (13) | lead generation | University of Latvia | Threat Intelligence (L) | no | 0.348 (10) | 0.500 | – | no message (no role preference)
Latvia | LV-2 (11) | employer | University of Latvia | Legal, Policy & Compliance (L) | no | 0.462 (6) | 0.450 | – | no message (no role preference)
Malta | MT-1 (27) | employer | University of Malta | Forensics (L) | no | 0.722 (4) | 0.000 | 0 | no gap
Malta | MT-2 (11) | employer | University of Malta | Risk Manager (L) | no | 0.750 (3) | 0.353 | – | no message (no role preference)
Poland | PL-1 (10) | employer | Rzeszów University of Technology | Researcher (L) | no | 0.167 (11) | 0.800 | 6 (3) | mission
Portugal | PT-1 (15) | consultancy + recruitment | Polytechnic of Leiria | Penetration Tester (L) | yes | 0.435 (3) | 0.618 | 4 (1) | confirm
Portugal | PT-2 (12) | staffing (IT outsourcing) | Polytechnic of Leiria | Forensics (L) | yes | 0.611 (1) | 0.698 | 4 (1) | confirm
Romania | RO-1 (26) | employer | Technical University of Cluj-Napoca | Threat Intelligence (L) | no | 0.435 (10) | 0.333 | 1 (0) | mission
Romania | RO-2 (13) | employer | Technical University of Cluj-Napoca | Penetration Tester (T) | no | 0.391 (12) | 0.500 | 3 (3) | mission
Slovakia | SK-1 (22) | employer | Technical University of Košice | Implementer (L) | no | 0.389 (2) | 0.625 | 5 (2) | mission
Slovakia | SK-2 (17) | employer | Technical University of Košice | Researcher (L) | no | 0.000 (9) | 1.000 | 6 (4) | mission
Slovakia | SK-3 (10) | employer | Technical University of Košice | Legal, Policy & Compliance (L) | no | 0.000 (9) | 1.000 | 8 (4) | mission
Slovenia | SI-1 (13) | aggregator | University of Novo Mesto | Threat Intelligence (L) | no | 0.652 (9) | 0.560 | – | no message (no role preference)
Slovenia | SI-2 (12) | lead generation | University of Novo Mesto | Incident Responder (L) | no | 0.474 (12) | 0.800 | – | no message (no role preference)
Slovenia | SI-3 (51)¹ | international organisation | University of Novo Mesto | CISO (L) | no | 0.889 (2) | 0.046 | 1 (0) | mission
Spain | ES-1 (19)² | employer | University of Alcalá | Legal, Policy & Compliance (L) | no | 0.385 (11) | 0.273 | 1 (1) | mission
Sweden | SE-1 (30) | employer | KTH Royal Institute of Technology | Architect (T) | yes | 0.840 (1) | 0.075 | 2 (1) | confirm
Sweden | SE-2 (10) | employer | KTH Royal Institute of Technology | Threat Intelligence (L) | no | 0.609 (10) | 0.333 | – | no message (no role preference)""".splitlines()
PAPER_TABLE_7 = {"FOR578": "+0.217 | 1 of 4 | 0.378 | –", "SEC599": "+0.217 | 1 of 4 | 0.364 | –",
                 "FOR589": "+0.130 | 1 of 4 | 0.448 | –", "SEC503": "+0.087 | 0 of 4 | 0.503 | –",
                 "SEC403": "+0.087 | 2 of 4 | 0.371 | 0.130", "SEC501": "+0.043 | 1 of 4 | 0.510 | 0.261",
                 "FOR498": "0.000 | 0 of 4 | 0.573 | 0.217", "FOR518": "0.000 | 0 of 4 | 0.573 | 0.304",
                 "LDR521": "0.000 | 0 of 4 | 0.573 | 0.087", "SEC497": "0.000 | 0 of 4 | 0.573 | 0.130",
                 "SEC530": "0.000 | 0 of 4 | 0.573 | 0.174", "SEC588": "0.000 | 0 of 4 | 0.573 | 0.304"}


def fixed(value, digits=3):
    return f"{value:.{digits}f}"


def signed(value):
    return "0.000" if abs(value) < 5e-4 else f"{value:+.3f}"


def percent(before, after):
    return f"{round(100 * (before - after) / before)}%"


def rows(record):
    """(name, value printed in the paper, value of the record) for every number compared."""

    TAU, ENDS, pairs, candidates = record["tau"], record["ends"], record["pairs"], record["candidates"]
    derived, rule, recorded_loop = record["derived"], record["rule"], record["loop"]
    MIN_ADS, INTERNATIONAL_ORGANISATIONS = rule["minimum_ads"], set(rule["international_organisations"])
    at_ends = {end: record["pairs_at_ends"][str(end)] for end in ENDS}
    by_code = {r["code"]: r for r in pairs}
    hu2, audit_sentence_ads = by_code["HU-2"], derived["audit_sentence_ads"]
    statement_text = {e["statement_id"]: e["statement"] for r in pairs for e in r["message"]}
    loop_case, message_ids = {"code": recorded_loop["case"]}, recorded_loop["message"]
    loop_targets, loop_controls = recorded_loop["targets"], recorded_loop["controls"]
    loop = {code: {**entry, "ends": {end: entry["ends"][str(end)] for end in ENDS}}
            for code, entry in recorded_loop["courses"].items()}
    combination = {**recorded_loop["combination"],
                   "ends": {end: recorded_loop["combination"]["ends"][str(end)] for end in ENDS}}

    paper = []
    for printed, r in zip(PAPER_S4, sorted(pairs, key=lambda p: (p["country"], p["rank"]))):
        international = r["company"] in INTERNATIONAL_ORGANISATIONS
        mark = "¹" if international else "²" if derived["single_title"][r["code"]] else ""
        message = ("–" if r["type"] == "no message" else
                   "0" if not r["message"] else f"{len(r['message'])} ({sum(e['unique'] for e in r['message'])})")
        kind = "international organisation" if international else r["kind"]
        now = " | ".join([r["country"], f"{r['code']} ({r['n']}){mark}", kind, S4_UNIVERSITY[r["programme"]],
                          f"{S4_ROLE[r['role']]} ({'T' if r['titled_role'] else 'L'})", "yes" if r["declared_role"] else "no",
                          f"{fixed(r['coverage_role'])} ({r['place_of_role']})", fixed(r["gap"]), message,
                          "no message (no role preference)" if r["type"] == "no message" else r["type"]])
        paper.append((f"Table S4 {printed.split(' | ')[1]}", printed, now))

    employers = [r for r in pairs if r["kind"] == "employer"]
    types = ["confirm", "mission", "no gap", "no message"]
    mission_gaps = [r["gap"] for r in pairs if r["type"] == "mission"]
    small = sum(1 for r in pairs if MIN_ADS <= r["n"] <= 14)
    be1, si3 = by_code["BE-1"], by_code["SI-3"]
    se1, ie2 = by_code["SE-1"], by_code["IE-2"]
    es1 = by_code["ES-1"]
    es1_locations, es1_texts = derived["es1_locations"], derived["es1_texts"]
    case_codes = set(derived["cases"])
    keeps_cases = all(e["role"] == r["role"] and e["type"] == r["type"]
                      for t in ENDS for e, r in zip(at_ends[t], pairs) if r["code"] in case_codes)
    gain_one = sum(1 for e, r in zip(at_ends[ENDS[1]], pairs)
                   if r["code"] in case_codes and len(e["message"]) == len(r["message"]) + 1)
    best_loop_score = derived["best_loop_course_similarity"]
    paper += [
        ("top three advertisers of each country", "81", str(len(candidates))),
        ("of them with at least ten in their country", "40", str(sum(c["ads"] >= MIN_ADS for c in candidates))),
        ("sets with the curriculum in CyberHEAD, countries", "31, 17", f"{len(pairs)}, {len({r['country'] for r in pairs})}"),
        ("employers, intermediaries", "22, 9", f"{len(employers)}, {len(pairs) - len(employers)}"),
        ("sets of ten to fourteen advertisements", "20 of 31", f"{small} of {len(pairs)}"),
        ("one advertisement in a set of 14 and of 10", "0.07 to 0.10", f"{fixed(1 / 14, 2)} to {fixed(1 / 10, 2)}"),
        ("BE-1: advertisements, in Belgium", "32, 22",
         f"{be1['n']}, {derived['be1_in_belgium']}"),
        ("SI-3: advertisements, countries", "51, 23", f"{si3['n']}, {derived['si3_countries']}"),
        ("sets whose titles name a role", "4 of 31", f"{sum(1 for r in pairs if r['titled_role'])} of {len(pairs)}"),
        ("sets by lift with no role above 1", "7", str(sum(1 for r in pairs if not r["titled_role"] and r["no_preference"]))),
        ("Table 6 employers / sets: confirm, mission, no gap, no message", "3/5, 13/16, 3/3, 3/7",
         ", ".join(f"{sum(1 for r in employers if r['type'] == t)}/{sum(1 for r in pairs if r['type'] == t)}" for t in types)),
        ("strengthen messages", "0", str(sum(1 for r in pairs if r["type"] == "strengthen"))),
        ("G of the mission messages, range", "0.046 to 1.000", f"{fixed(min(mission_gaps))} to {fixed(max(mission_gaps))}"),
        ("lowest: SI-3, role", "SI-3, CISO", next(f"{r['code']}, {r['role']}" for r in pairs if r["type"] == "mission" and r["gap"] == min(mission_gaps))),
        ("highest: sets", "SK-2, SK-3", ", ".join(r["code"] for r in pairs if r["type"] == "mission" and r["gap"] == max(mission_gaps))),
        ("ES-1: one title, advertisements, locations, texts", "yes, 19, 18, 5",
         f"{'yes' if derived['single_title']['ES-1'] else 'no'}, {es1['n']}, {es1_locations}, {es1_texts}"),
        ("SE-1: role, titles naming it", "Architect, 8 of 30", f"{se1['role']}, {se1['titled_counts'].get(se1['role'], 0)} of {se1['n']}"),
        ("SE-1: declared, C(r), place", "yes, 0.840, 1", f"{'yes' if se1['declared_role'] else 'no'}, {fixed(se1['coverage_role'])}, {se1['place_of_role']}"),
        ("SE-1: message", "Security architecture reference models 0.467; Legal, regulatory and legislative compliance requirements, recommendations and best practices 0.233",
         "; ".join(f"{e['statement']} {fixed(e['share'])}" for e in se1["message"])),
        ("SE-1: G", "0.075", fixed(se1["gap"])),
        ("IE-2: role, titles naming it", "PenTester, 2 of 10", f"{ie2['role']}, {ie2['titled_counts'].get(ie2['role'], 0)} of {ie2['n']}"),
        ("IE-2: declared, message, sentence", "yes, Develop codes, scripts and programmes, Experience with scripting.",
         f"{'yes' if ie2['declared_role'] else 'no'}, " + "; ".join(f"{e['statement']}, {e['sentence']}" for e in ie2["message"])),
        ("BE-1: titles name a role", "no", "yes" if be1["titled_role"] else "no"),
        ("BE-1: role by lift, lift", "ThreatIntel, 1.87", f"{be1['lift_first']}, {fixed(be1['lift'][be1['lift_first']], 2)}"),
        ("BE-1: declared, place, C(r)", "no, 11, 0.348", f"{'yes' if be1['declared_role'] else 'no'}, {be1['place_of_role']}, {fixed(be1['coverage_role'])}"),
        ("BE-1: message, G", "4, 0.573", f"{len(be1['message'])}, {fixed(be1['gap'])}"),
        ("BE-1: unique statements", "Cross-domain and border-domain knowledge related to cybersecurity 0.281; Cyber threat actors 0.250",
         "; ".join(f"{e['statement']} {fixed(e['share'])}" for e in be1["message"] if e["unique"])),
        ("BE-1: shared statements", "0.625, 0.562", ", ".join(fixed(e["share"]) for e in be1["message"] if not e["unique"])),
        ("HU-2: kind, role, place, C(r)", "agency (RPO), Auditor, 12, 0.500",
         f"{hu2['kind']}, {hu2['role']}, {hu2['place_of_role']}, {fixed(hu2['coverage_role'])}"),
        ("HU-2: message statements, each required by", "3, 0.650", f"{len(hu2['message'])}, " + "/".join(sorted({fixed(e['share']) for e in hu2['message']}))),
        ("HU-2: the sentence behind them", "Audit experience.", "/".join(sorted({e["sentence"] for e in hu2["message"]}))),
        ("HU-2: advertisements with that sentence", "13 of 20", f"{audit_sentence_ads} of {hu2['n']}"),
        ("at 0.580 and 0.595 the four pairs of Figure 8 keep role and type", "yes", "yes" if keeps_cases else "no"),
        ("of their messages, gaining one statement at 0.595", "2", str(gain_one)),
        ("loop case, messages of SE-1 and IE-2", "BE-1 4, SE-1 2, IE-2 1",
         f"{loop_case['code']} {len(message_ids)}, SE-1 {len(se1['message'])}, IE-2 {len(ie2['message'])}"),
        ("loop target courses, controls", "4, 8", f"{len(loop_targets)}, {len(loop_controls)}"),
        ("G before", "0.573", fixed(loop[loop_targets[0]]["gap_before"])),
    ]
    for code in loop_targets + loop_controls:
        row = loop[code]
        paper.append((f"Table 7 {code}", PAPER_TABLE_7[code],
                      f"{signed(row['delta'])} | {row['message_covered']} of {len(message_ids)} | {fixed(row['gap_after'])} | "
                      + ("–" if row["ceiling"] is None else fixed(row["ceiling"]))))
    step = 1 / derived["role_statements"]
    covers_actors = [c for c in loop_targets if any(statement_text[s] == "Cyber threat actors" for s in loop[c]["message_covered_ids"])]
    sec403_ids = {statement_text[s] for s in loop["SEC403"]["message_covered_ids"]}
    target_ids = {statement_text[s] for c in loop_targets for s in loop[c]["message_covered_ids"]}
    uncovered_after = [statement_text[s] for s in message_ids if s not in combination["message_covered_ids"]]
    paper += [
        ("Table 7 combination", "SEC599 + SEC403 | +0.304 | 3 of 4 | 0.161",
         f"{' + '.join(combination['courses'])} | {signed(combination['delta'])} | "
         f"{combination['message_covered']} of {len(message_ids)} | {fixed(combination['gap_after'])}"),
        ("target courses raising the role, in statements", "4, 2 to 5",
         f"{sum(1 for c in loop_targets if loop[c]['delta'] > 1e-9)}, {round(min(loop[c]['delta'] for c in loop_targets) / step)} "
         f"to {round(max(loop[c]['delta'] for c in loop_targets) / step)}"),
        ("target courses covering Cyber threat actors", "3", str(len(covers_actors))),
        ("FOR578, SEC599: reduction of G", "34%, 37%", ", ".join(percent(loop[c]["gap_before"], loop[c]["gap_after"]) for c in ("FOR578", "SEC599"))),
        ("controls unchanged, within their ceiling", "6, all",
         f"{sum(1 for c in loop_controls if loop[c]['delta'] < 1e-9)}, "
         + ("all" if all(loop[c]["delta"] <= loop[c]["ceiling"] + 1e-9 for c in loop_controls) else "not all")),
        ("SEC403: reduction of G", "35%", percent(loop["SEC403"]["gap_before"], loop["SEC403"]["gap_after"])),
        ("SEC403 covers, no target course covers", "Communicate, present and report to relevant stakeholders; Cross-domain and border-domain knowledge related to cybersecurity",
         "; ".join(sorted(sec403_ids - target_ids))),
        ("SEC501 covers the cross-domain statement", "yes",
         "yes" if "Cross-domain and border-domain knowledge related to cybersecurity" in {statement_text[s] for s in loop["SEC501"]["message_covered_ids"]} else "no"),
        ("combination: reduction of G", "72%", percent(combination["gap_before"], combination["gap_after"])),
        ("at 0.580: FOR578, SEC599, combination", "35%, 37%, 71%",
         ", ".join(percent(x["gap_before"], x["gap_after"]) for x in
                   (loop["FOR578"]["ends"][ENDS[0]], loop["SEC599"]["ends"][ENDS[0]], combination["ends"][ENDS[0]]))),
        ("at 0.595: every target raises the role", "yes", "yes" if all(loop[c]["ends"][ENDS[1]]["delta"] > 1e-9 for c in loop_targets) else "no"),
        ("at 0.595: controls within their ceiling", "yes",
         "yes" if all(loop[c]["ends"][ENDS[1]]["delta"] <= loop[c]["ceiling"] + 1e-9 for c in loop_controls) else "no"),
        ("at 0.595: FOR578, SEC599", "21%, 29%",
         ", ".join(percent(loop[c]["ends"][ENDS[1]]["gap_before"], loop[c]["ends"][ENDS[1]]["gap_after"]) for c in ("FOR578", "SEC599"))),
        ("at 0.595: combination", "65% (0.568 to 0.197)",
         f"{percent(combination['ends'][ENDS[1]]['gap_before'], combination['ends'][ENDS[1]]['gap_after'])} "
         f"({fixed(combination['ends'][ENDS[1]]['gap_before'])} to {fixed(combination['ends'][ENDS[1]]['gap_after'])})"),
        ("overview: FOR578 and SEC599 the same effect", "yes",
         "yes" if all(abs(loop[c]["narrow"]["delta"] - loop[c]["delta"]) < 1e-9 and
                      abs(loop[c]["narrow"]["gap_after"] - loop[c]["gap_after"]) < 1e-9 for c in ("FOR578", "SEC599")) else "no"),
        ("overview: FOR589 and SEC503 no longer raise the role", "yes",
         "yes" if all(loop[c]["narrow"]["delta"] < 1e-9 for c in ("FOR589", "SEC503")) else "no"),
        ("overview: combination", "48% (0.573 to 0.301)",
         f"{percent(combination['narrow']['gap_before'], combination['narrow']['gap_after'])} "
         f"({fixed(combination['narrow']['gap_before'])} to {fixed(combination['narrow']['gap_after'])})"),
        ("overview: SEC403 message statements", "1", str(loop["SEC403"]["narrow"]["message_covered"])),
        ("left after the combination", "Communicate, coordinate and cooperate with internal and external stakeholders",
         "; ".join(uncovered_after)),
        ("covered by none of the courses of the loop", "yes", "yes" if best_loop_score < TAU else "no"),
    ]

    return paper
