from app.scoring import build_roadmap, readiness_label, score_resume


ROLE = {"Python": 3, "Docker": 2, "Kubernetes": 1}


def test_full_match_scores_100():
    skills = {k: {"evidence": "applied", "category": "x"} for k in ROLE}
    assert score_resume(skills, ROLE)["score"] == 100.0


def test_listed_skills_get_partial_credit():
    skills = {"Python": {"evidence": "listed", "category": "x"}}
    assert score_resume(skills, ROLE)["score"] == round(100 * 3 * 0.7 / 6, 1)


def test_missing_sorted_by_weight_and_roadmap():
    result = score_resume({}, ROLE)
    assert [m["skill"] for m in result["missing"]] == ["Python", "Docker", "Kubernetes"]
    plan = build_roadmap(result["missing"])
    assert plan[0]["skill"] == "Python" and plan[0]["priority"] == "core"


def test_labels():
    assert readiness_label(85) == "Interview ready" and readiness_label(5) == "Early stage"
