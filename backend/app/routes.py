from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func, select

from .models import Analysis, Role
from .parser import extract_text, parse_resume
from .ratelimit import rate_limited
from .scoring import build_roadmap, resume_tips, score_resume

api = Blueprint("api", __name__)
MAX_TEXT_CHARS = 60_000


@api.get("/health")
def health():
    return jsonify(status="ok")


@api.get("/roles")
def roles():
    with current_app.session_factory() as s:
        rows = s.scalars(select(Role).order_by(Role.name)).all()
        return jsonify([{"key": r.key, "name": r.name, "skill_count": len(r.skills)} for r in rows])


@api.post("/analyze")
@rate_limited
def analyze():
    role_key = (request.form.get("role") or (request.get_json(silent=True) or {}).get("role") or "").strip()
    if not role_key:
        return jsonify(error="Please choose a target role."), 400

    try:
        if "file" in request.files and request.files["file"].filename:
            f = request.files["file"]
            text = extract_text(f.read(), f.filename)
        else:
            payload = request.get_json(silent=True) or {}
            text = request.form.get("text") or payload.get("text") or ""
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except Exception:
        current_app.logger.exception("resume read failed")
        return jsonify(error="Could not read that file. Try a text-based PDF or DOCX."), 400

    text = text[:MAX_TEXT_CHARS]
    if len(text.split()) < 30:
        return jsonify(error="Not enough text found in the resume. If it is a scanned PDF, upload a text-based version."), 400

    with current_app.session_factory() as s:
        role = s.scalar(select(Role).where(Role.key == role_key))
        if role is None:
            return jsonify(error="Unknown role."), 404
        role_skills = {rs.skill: rs.weight for rs in role.skills}
        role_name = role.name

        parsed = parse_resume(text, current_app.config["SPACY_MODEL"])
        result = score_resume(parsed.skills, role_skills)
        s.add(Analysis(role_key=role_key, score=result["score"],
                       matched_count=len(result["matched"]), missing_count=len(result["missing"])))
        s.commit()

    return jsonify({
        "role": {"key": role_key, "name": role_name},
        "job_readiness_score": result["score"],
        "readiness_label": result["label"],
        "matched_skills": result["matched"],
        "missing_skills": result["missing"],
        "extra_skills": result["extra_skills"],
        "roadmap": build_roadmap(result["missing"]),
        "resume_tips": resume_tips(parsed),
        "detected_sections": parsed.sections,
    })


@api.get("/history")
def history():
    with current_app.session_factory() as s:
        rows = s.scalars(select(Analysis).order_by(Analysis.id.desc()).limit(10)).all()
        return jsonify([{"role": r.role_key, "score": r.score, "created_at": r.created_at.isoformat()} for r in rows])


@api.get("/stats")
def stats():
    """Aggregate usage metrics (no personal data is stored, so none is exposed)."""
    with current_app.session_factory() as s:
        rows = s.execute(
            select(Analysis.role_key, func.count(Analysis.id), func.avg(Analysis.score)).group_by(Analysis.role_key)
        ).all()
        by_role = {k: {"analyses": n, "average_score": round(float(avg), 1)} for k, n, avg in rows}
        total = sum(v["analyses"] for v in by_role.values())
        return jsonify(total_analyses=total, by_role=by_role)
