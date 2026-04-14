from __future__ import annotations

import re
from dataclasses import dataclass


STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "your",
}

SENIORITY_TARGET_YEARS = {
    "entry": 1.5,
    "mid": 4.0,
    "senior": 6.0,
    "staff": 8.0,
    "principal": 10.0,
}


@dataclass
class EvidenceMatch:
    phrase: str
    source: str
    evidence: str
    score: float


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def normalize_token(token: str) -> str:
    value = str(token or "").strip().lower()
    if len(value) > 4 and value.endswith("ies"):
        return value[:-3] + "y"
    if len(value) > 4 and value.endswith("ers"):
        return value[:-1]
    if len(value) > 4 and value.endswith("s") and not value.endswith("ss"):
        return value[:-1]
    return value


def tokenize(value: str) -> set[str]:
    return {
        normalize_token(token)
        for token in normalize_text(value).split()
        if len(token) > 2 and token not in STOPWORDS
    }


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def sentence_case(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text[0].upper() + text[1:]


def build_candidate_evidence(candidate: dict) -> list[dict]:
    evidence = []

    for skill in candidate.get("core_skills", []) or []:
        evidence.append(
            {
                "label": f"Core skill: {skill}",
                "text": skill,
            }
        )

    for item in candidate.get("differentiators", []) or []:
        evidence.append(
            {
                "label": f"Differentiator: {item}",
                "text": item,
            }
        )

    for role in candidate.get("target_roles", []) or []:
        evidence.append(
            {
                "label": f"Target role: {role}",
                "text": role,
            }
        )

    for project in candidate.get("projects", []) or []:
        joined = " ".join(
            [
                str(project.get("name") or ""),
                str(project.get("summary") or ""),
                str(project.get("outcome") or ""),
                " ".join(project.get("skills", []) or []),
            ]
        )
        evidence.append(
            {
                "label": f"Project: {project.get('name', 'Project')}",
                "text": joined,
            }
        )

    return evidence


def phrase_match_score(phrase: str, candidate_evidence: list[dict]) -> EvidenceMatch | None:
    phrase_text = normalize_text(phrase)
    phrase_tokens = tokenize(phrase)
    if not phrase_text or not phrase_tokens:
        return None

    best_match = None
    for entry in candidate_evidence:
        haystack_text = normalize_text(entry.get("text", ""))
        haystack_tokens = tokenize(entry.get("text", ""))
        if not haystack_text or not haystack_tokens:
            continue

        overlap = len(phrase_tokens & haystack_tokens) / len(phrase_tokens)
        exact_bonus = 0.25 if phrase_text in haystack_text else 0.0
        score = clamp(overlap + exact_bonus, 0.0, 1.0)
        if best_match is None or score > best_match.score:
            best_match = EvidenceMatch(
                phrase=phrase,
                source=str(entry.get("label", "Candidate evidence")),
                evidence=str(entry.get("text", "")),
                score=score,
            )

    if best_match and best_match.score >= 0.42:
        return best_match
    return None


def summarize_match(match: EvidenceMatch) -> str:
    evidence = sentence_case(match.evidence.strip())
    if len(evidence) > 135:
        evidence = evidence[:132].rstrip() + "..."
    return f"{match.phrase} -> {match.source}. {evidence}"


def match_list(phrases: list[str], candidate_evidence: list[dict]) -> tuple[list[EvidenceMatch], list[str]]:
    matched = []
    missing = []
    for phrase in phrases or []:
        result = phrase_match_score(phrase, candidate_evidence)
        if result is None:
            missing.append(phrase)
        else:
            matched.append(result)
    matched.sort(key=lambda item: item.score, reverse=True)
    return matched, missing


def score_location(candidate: dict, job: dict) -> tuple[float, str]:
    preferences = [normalize_text(item) for item in candidate.get("location_preferences", []) or []]
    job_location = normalize_text(job.get("location", ""))
    remote_policy = normalize_text(job.get("remote_policy", ""))

    if "remote" in preferences and "remote" in remote_policy:
        return 1.0, "Remote preference is directly supported."

    if job_location and any(pref and pref in job_location for pref in preferences if pref != "remote"):
        return 1.0, f"Location aligns with stated preference: {job.get('location', '')}."

    if "remote" in remote_policy:
        return 0.82, "Remote policy keeps the role viable even without a location match."

    if "hybrid" in remote_policy:
        return 0.65, "Hybrid setup is workable but not ideal for the stated location preference."

    return 0.35, "Location is likely to require a compromise."


def score_comp(candidate: dict, job: dict) -> tuple[float, str]:
    salary_floor = float(candidate.get("salary_floor_gbp", 0) or 0)
    salary_max = float(job.get("salary_max_gbp", 0) or 0)

    if salary_max <= 0:
        return 0.55, "Compensation is not listed, so the role stays viable but unconfirmed."

    if salary_floor <= 0:
        return 0.8, "Compensation looks healthy against the sample profile."

    ratio = salary_max / salary_floor
    if ratio >= 1.15:
        return 1.0, "Compensation clears the candidate floor with room to negotiate."
    if ratio >= 1.0:
        return 0.82, "Compensation meets the stated floor."
    if ratio >= 0.9:
        return 0.58, "Compensation is close, but there is little room for tradeoff."
    return 0.32, "Compensation sits below the sample floor."


def score_experience(candidate: dict, job: dict) -> tuple[float, str]:
    years = float(candidate.get("experience_years", 0) or 0)
    target = SENIORITY_TARGET_YEARS.get(normalize_text(job.get("seniority", "")), 5.0)
    ratio = years / target if target else 1.0
    score = clamp(0.35 + (min(ratio, 1.2) / 1.2) * 0.65, 0.35, 1.0)

    if ratio >= 1.0:
        return score, f"Experience depth supports a {job.get('seniority', 'target')} role."
    if ratio >= 0.8:
        return score, f"Experience is close to the expected {job.get('seniority', 'target')} bar."
    return score, f"Experience is slightly light for the stated {job.get('seniority', 'target')} scope."


def score_focus(candidate: dict, job: dict) -> tuple[float, str]:
    candidate_text = " ".join(
        [
            candidate.get("headline", ""),
            candidate.get("summary", ""),
            " ".join(candidate.get("differentiators", []) or []),
            " ".join(
                " ".join(
                    [
                        project.get("summary", ""),
                        project.get("outcome", ""),
                        " ".join(project.get("skills", []) or []),
                    ]
                )
                for project in candidate.get("projects", []) or []
            ),
        ]
    )
    job_text = " ".join(
        [
            job.get("summary", ""),
            job.get("business_context", ""),
            " ".join(job.get("responsibilities", []) or []),
        ]
    )

    candidate_tokens = tokenize(candidate_text)
    job_tokens = tokenize(job_text)
    if not candidate_tokens or not job_tokens:
        return 0.45, "Focus alignment is hard to infer from the sample data."

    overlap = len(candidate_tokens & job_tokens) / max(8, len(job_tokens))
    score = clamp(0.42 + overlap * 3.0, 0.42, 1.0)
    if score >= 0.8:
        return score, "Role focus lines up with the candidate's strongest project themes."
    if score >= 0.65:
        return score, "Role focus is directionally aligned, with some translation required."
    return score, "Role focus is partially aligned but would need sharper positioning."


def build_strengths(job: dict, must_matches: list[EvidenceMatch], focus_note: str, comp_note: str) -> list[str]:
    strengths = [summarize_match(match) for match in must_matches[:3]]
    if len(strengths) < 3:
        strengths.append(f"Role context: {focus_note}")
    if len(strengths) < 3:
        strengths.append(f"Commercial fit: {comp_note}")
    return strengths[:3]


def build_risks(job: dict, missing_must: list[str], location_note: str, comp_note: str, experience_note: str) -> list[str]:
    risks = []
    for phrase in missing_must[:2]:
        risks.append(f"Missing direct evidence for {phrase}.")

    if "compromise" in location_note.lower():
        risks.append(location_note)
    if "below" in comp_note.lower() or "little room" in comp_note.lower():
        risks.append(comp_note)
    if "slightly light" in experience_note.lower():
        risks.append(experience_note)

    return risks[:3] or ["No critical risk surfaced in the simplified demo logic."]


def build_positioning(candidate: dict, job: dict, must_matches: list[EvidenceMatch], missing_must: list[str]) -> list[str]:
    projects = candidate.get("projects", []) or []
    anchor_project = projects[0].get("name", "the strongest project") if projects else "the strongest project"
    lead_strength = must_matches[0].phrase if must_matches else "end-to-end AI delivery"
    actions = [
        f"Lead with {lead_strength} and frame the profile as outcome-oriented rather than tool-first.",
        f"Anchor the story on {anchor_project} to make the fit concrete within the first minute.",
    ]
    if missing_must:
        actions.append(
            f"Address the gap on {missing_must[0]} directly: show adjacent evidence, then explain the ramp plan."
        )
    else:
        actions.append(
            f"Push for a scoped first-90-days conversation around {job.get('business_context', 'business impact')}."
        )
    return actions[:3]


def story_relevance(project: dict, job: dict) -> float:
    project_text = " ".join(
        [
            project.get("name", ""),
            project.get("summary", ""),
            project.get("outcome", ""),
            " ".join(project.get("skills", []) or []),
        ]
    )
    job_text = " ".join(
        [
            job.get("summary", ""),
            " ".join(job.get("must_have", []) or []),
            " ".join(job.get("responsibilities", []) or []),
        ]
    )
    project_tokens = tokenize(project_text)
    job_tokens = tokenize(job_text)
    if not project_tokens or not job_tokens:
        return 0.0
    overlap = len(project_tokens & job_tokens) / max(6, len(job_tokens))
    return clamp(overlap * 4.0, 0.0, 1.0)


def build_story_map(candidate: dict, job: dict) -> list[dict]:
    ranked = []
    for project in candidate.get("projects", []) or []:
        ranked.append((story_relevance(project, job), project))
    ranked.sort(key=lambda item: item[0], reverse=True)

    story_map = []
    for score, project in ranked[:2]:
        story_map.append(
            {
                "project_name": project.get("name", "Project"),
                "why_relevant": project.get("summary", ""),
                "interview_angle": (
                    "Use this story to show ownership, technical judgment, and measurable outcome."
                    if score >= 0.55
                    else "Useful as supporting evidence, but tighten the relevance before using it."
                ),
                "proof_point": project.get("outcome", ""),
            }
        )
    return story_map


def build_likely_questions(job: dict, risks: list[str]) -> list[str]:
    questions = [f"Why this role: {job.get('title', 'the role')} at {job.get('company', 'this company')}?"]
    for phrase in (job.get("must_have", []) or [])[:3]:
        questions.append(f"Can you walk through a concrete example of {phrase}?")
    if risks:
        questions.append(f"How would you de-risk {risks[0].rstrip('.')} in your first 90 days?")
    return questions[:5]


def build_due_diligence(job: dict) -> list[str]:
    return [
        f"Which business KPI does the {job.get('title', 'role')} directly influence?",
        "What does strong performance look like in the first 90 days?",
        "Where does ownership sit between product, data, and engineering on this team?",
    ]


def fit_snapshot(candidate: dict, job: dict) -> dict:
    candidate_evidence = build_candidate_evidence(candidate)
    must_matches, missing_must = match_list(job.get("must_have", []) or [], candidate_evidence)
    nice_matches, missing_nice = match_list(job.get("nice_to_have", []) or [], candidate_evidence)

    skill_ratio = 0.0
    if job.get("must_have"):
        must_ratio = len(must_matches) / len(job.get("must_have", []))
        nice_ratio = len(nice_matches) / max(1, len(job.get("nice_to_have", []) or []))
        skill_ratio = clamp(must_ratio * 0.78 + nice_ratio * 0.22, 0.0, 1.0)

    experience_score, experience_note = score_experience(candidate, job)
    focus_score, focus_note = score_focus(candidate, job)
    location_score, location_note = score_location(candidate, job)
    comp_score, comp_note = score_comp(candidate, job)

    weighted = (
        skill_ratio * 0.40
        + experience_score * 0.15
        + focus_score * 0.15
        + location_score * 0.15
        + comp_score * 0.15
    )
    fit_score = int(round(weighted * 100))

    if fit_score >= 80:
        readiness = "Strong fit"
    elif fit_score >= 68:
        readiness = "Selective fit"
    elif fit_score >= 55:
        readiness = "Stretch fit"
    else:
        readiness = "Low-fit demo case"

    strengths = build_strengths(job, must_matches, focus_note, comp_note)
    risks = build_risks(job, missing_must, location_note, comp_note, experience_note)
    positioning = build_positioning(candidate, job, must_matches, missing_must)

    return {
        "candidate_id": candidate.get("id", ""),
        "job_id": job.get("id", ""),
        "fit_score": fit_score,
        "readiness": readiness,
        "component_scores": {
            "skills": int(round(skill_ratio * 100)),
            "experience": int(round(experience_score * 100)),
            "focus": int(round(focus_score * 100)),
            "location": int(round(location_score * 100)),
            "comp": int(round(comp_score * 100)),
        },
        "strong_matches": strengths,
        "risks": risks,
        "positioning_advice": positioning,
        "evidence_grid": [
            {
                "requirement": match.phrase,
                "source": match.source,
                "evidence": sentence_case(match.evidence),
            }
            for match in must_matches[:4]
        ],
        "gap_grid": missing_must[:3],
        "notes": {
            "experience": experience_note,
            "focus": focus_note,
            "location": location_note,
            "comp": comp_note,
            "missing_nice": missing_nice[:2],
        },
    }


def compare_jobs(candidate: dict, jobs: list[dict]) -> dict:
    snapshots = []
    for job in jobs:
        snapshot = fit_snapshot(candidate, job)
        snapshots.append({"job": job, "snapshot": snapshot})

    snapshots.sort(key=lambda item: item["snapshot"]["fit_score"], reverse=True)

    ranked = []
    for index, item in enumerate(snapshots, start=1):
        job = item["job"]
        snapshot = item["snapshot"]
        strongest = snapshot["strong_matches"][0] if snapshot["strong_matches"] else "Balanced opportunity."
        main_risk = snapshot["risks"][0] if snapshot["risks"] else "No major risk."
        has_location_compromise = any("compromise" in risk.lower() for risk in snapshot["risks"])

        if snapshot["fit_score"] >= 80:
            posture = "Prioritize now"
            if has_location_compromise:
                posture = "Keep active"
        elif snapshot["fit_score"] >= 68:
            posture = "Keep active"
        elif snapshot["fit_score"] >= 55:
            posture = "Use as stretch"
        else:
            posture = "Deprioritize"

        ranked.append(
            {
                "rank": index,
                "job_id": job.get("id", ""),
                "company": job.get("company", ""),
                "title": job.get("title", ""),
                "fit_score": snapshot["fit_score"],
                "readiness": snapshot["readiness"],
                "posture": posture,
                "tradeoff": f"{strongest} Watchout: {main_risk}",
            }
        )

    top = ranked[0]
    summary = [
        f"Start with {top['company']} - {top['title']} because it has the strongest balance of fit, scope, and practical viability.",
    ]
    if len(ranked) > 1:
        second = ranked[1]
        summary.append(
            f"Keep {second['company']} - {second['title']} active as the next best option, especially if you want a different risk/reward mix."
        )
    if len(ranked) > 2:
        third = ranked[2]
        summary.append(
            f"Treat {third['company']} - {third['title']} as a stretch lane unless new evidence closes the current gap."
        )

    return {
        "ranking": ranked,
        "summary": summary,
    }


def interview_prep(candidate: dict, job: dict) -> dict:
    snapshot = fit_snapshot(candidate, job)
    story_map = build_story_map(candidate, job)
    risks = snapshot["risks"]

    prep_focus = [
        f"Prepare a tight opening pitch around {snapshot['strong_matches'][0].split('->')[0].strip()}."
        if snapshot["strong_matches"]
        else "Prepare a tight opening pitch around your most relevant project.",
        f"Expect depth on {job.get('must_have', ['technical judgment'])[0]} and bring one measurable example."
        if job.get("must_have")
        else "Expect a technical deep dive and bring one measurable example.",
    ]
    if risks:
        prep_focus.append(f"Have a clean mitigation answer for: {risks[0]}")

    return {
        "fit_snapshot": snapshot,
        "likely_questions": build_likely_questions(job, risks),
        "story_map": story_map,
        "prep_focus": prep_focus,
        "due_diligence": build_due_diligence(job),
    }


def bar_width(value: int) -> str:
    return f"{max(4, min(100, int(value)))}%"


def compact_company_title(job: dict) -> str:
    return f"{job.get('company', 'Company')} - {job.get('title', 'Role')}"


def fit_snapshot_markdown(candidate: dict, job: dict, snapshot: dict) -> str:
    lines = [
        f"# Fit Snapshot: {job.get('company', '')} - {job.get('title', '')}",
        "",
        f"- Candidate: {candidate.get('name', '')}",
        f"- Readiness: {snapshot.get('readiness', '')}",
        f"- Fit score: {snapshot.get('fit_score', '')}/100",
        f"- Location: {job.get('location', '')} | {job.get('remote_policy', '')}",
        "",
        "## Component Scores",
        "",
    ]
    for key, value in snapshot.get("component_scores", {}).items():
        lines.append(f"- {key.title()}: {value}")

    lines.extend(["", "## Strong Matches", ""])
    for item in snapshot.get("strong_matches", []):
        lines.append(f"- {item}")

    lines.extend(["", "## Risks", ""])
    for item in snapshot.get("risks", []):
        lines.append(f"- {item}")

    lines.extend(["", "## Positioning Advice", ""])
    for item in snapshot.get("positioning_advice", []):
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def comparison_markdown(candidate: dict, comparison: dict) -> str:
    lines = [
        f"# Offer Comparison: {candidate.get('name', '')}",
        "",
        "## Recommendation",
        "",
    ]
    for item in comparison.get("summary", []):
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Ranking",
            "",
            "| Rank | Company | Role | Fit Score | Posture | Tradeoff |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in comparison.get("ranking", []):
        lines.append(
            f"| {row.get('rank', '')} | {row.get('company', '')} | {row.get('title', '')} | {row.get('fit_score', '')} | {row.get('posture', '')} | {row.get('tradeoff', '')} |"
        )
    return "\n".join(lines) + "\n"


def interview_prep_markdown(candidate: dict, job: dict, prep: dict) -> str:
    lines = [
        f"# Interview Prep Brief: {job.get('company', '')} - {job.get('title', '')}",
        "",
        f"- Candidate: {candidate.get('name', '')}",
        f"- Fit score: {prep.get('fit_snapshot', {}).get('fit_score', '')}/100",
        "",
        "## Likely Questions",
        "",
    ]
    for item in prep.get("likely_questions", []):
        lines.append(f"- {item}")

    lines.extend(["", "## Prep Focus", ""])
    for item in prep.get("prep_focus", []):
        lines.append(f"- {item}")

    lines.extend(["", "## Due Diligence", ""])
    for item in prep.get("due_diligence", []):
        lines.append(f"- {item}")

    lines.extend(["", "## Story Map", ""])
    for item in prep.get("story_map", []):
        lines.append(f"- {item.get('project_name', '')}: {item.get('proof_point', '')}")

    return "\n".join(lines) + "\n"
