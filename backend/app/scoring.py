"""Job Readiness Score, skill-gap report and learning roadmap."""
from .skills_data import DEFAULT_RESOURCE, RESOURCES

TIER = {3: "core", 2: "important", 1: "bonus"}
CREDIT = {"applied": 1.0, "listed": 0.7}  # a skill shown in projects/experience counts fully
BANDS = [(80, "Interview ready"), (60, "Strong foundation"), (40, "Developing"), (0, "Early stage")]


def readiness_label(score: float) -> str:
    return next(label for cutoff, label in BANDS if score >= cutoff)


def score_resume(parsed_skills: dict, role_skills: dict) -> dict:
    total = sum(role_skills.values())
    earned = 0.0
    matched, missing = [], []
    for skill, weight in role_skills.items():
        info = parsed_skills.get(skill)
        if info:
            credit = CREDIT[info["evidence"]]
            earned += weight * credit
            matched.append({"skill": skill, "tier": TIER[weight], "evidence": info["evidence"]})
        else:
            missing.append({"skill": skill, "tier": TIER[weight], "weight": weight})
    missing.sort(key=lambda m: (-m["weight"], m["skill"]))
    extras = sorted(s for s in parsed_skills if s not in role_skills)
    score = round(100 * earned / total, 1) if total else 0.0
    return {
        "score": score,
        "label": readiness_label(score),
        "matched": sorted(matched, key=lambda m: (-{"core": 3, "important": 2, "bonus": 1}[m["tier"]], m["skill"])),
        "missing": [{"skill": m["skill"], "tier": m["tier"]} for m in missing],
        "extra_skills": extras,
    }


def build_roadmap(missing: list, max_items: int = 6) -> list:
    """Order gaps by importance and attach a concrete build task and a learning source."""
    plan = []
    for i, m in enumerate(missing[:max_items]):
        task, link = RESOURCES.get(m["skill"], DEFAULT_RESOURCE)
        weeks = 2 if m["tier"] == "core" else 1
        plan.append({
            "step": i + 1,
            "skill": m["skill"],
            "priority": m["tier"],
            "estimated_weeks": weeks,
            "build_task": task,
            "learn_from": link,
        })
    return plan


def resume_tips(parsed) -> list:
    tips = []
    if "skills" not in parsed.sections:
        tips.append("Add a clear 'Technical Skills' section so ATS parsers can read your skills.")
    if "projects" not in parsed.sections and "experience" not in parsed.sections:
        tips.append("Add Projects or Experience sections; skills shown in real work count more than a skills list.")
    if parsed.bullet_count and parsed.bullet_count < 6:
        tips.append("Add more bullet points that describe what you built and the result.")
    if parsed.date_ranges == 0:
        tips.append("Add dates (e.g. Jan 2025 – Jun 2025) to experience and projects.")
    if parsed.word_count < 150:
        tips.append("Your resume looks very short; add detail about projects and impact.")
    return tips
