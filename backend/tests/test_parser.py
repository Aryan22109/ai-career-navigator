from app.parser import parse_resume, split_sections


def test_extracts_skills_and_evidence(sample_text):
    parsed = parse_resume(sample_text)
    assert parsed.skills["Flask"]["evidence"] == "applied"
    assert "Python" in parsed.skills
    assert {"skills", "projects", "experience", "education"} <= set(parsed.sections)


def test_c_language_not_confused_with_cpp_or_grade():
    assert "C" in parse_resume("Skills\nC, C++, Python").skills
    assert "C" not in parse_resume("Skills\nPython\nI received a grade C in art").skills


def test_generic_testing_not_matched():
    assert "Testing" not in parse_resume("Skills\nStatistics, hypothesis testing").skills


def test_split_sections_detects_headings():
    s = split_sections("Name\nSKILLS\nPython\nProjects:\nBuilt things")
    assert "Python" in s["skills"] and "Built things" in s["projects"]
