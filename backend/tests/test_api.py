import io


def test_health_and_roles(client):
    assert client.get("/api/health").json == {"status": "ok"}
    keys = {r["key"] for r in client.get("/api/roles").json}
    assert {"sde", "ai_ml", "devops", "data_scientist"} <= keys


def test_analyze_text(client, sample_text):
    r = client.post("/api/analyze", json={"role": "sde", "text": sample_text})
    assert r.status_code == 200
    body = r.json
    assert 0 < body["job_readiness_score"] <= 100
    assert body["roadmap"] and body["missing_skills"]
    assert client.get("/api/history").json[0]["role"] == "sde"


def test_analyze_file_upload(client, sample_text):
    data = {"role": "sde", "file": (io.BytesIO(sample_text.encode()), "resume.txt")}
    r = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert r.status_code == 200


def test_validation_errors(client, sample_text):
    assert client.post("/api/analyze", json={"text": sample_text}).status_code == 400
    assert client.post("/api/analyze", json={"role": "nope", "text": sample_text}).status_code == 404
    assert client.post("/api/analyze", json={"role": "sde", "text": "too short"}).status_code == 400
    bad = {"role": "sde", "file": (io.BytesIO(b"x"), "resume.exe")}
    assert client.post("/api/analyze", data=bad, content_type="multipart/form-data").status_code == 400
