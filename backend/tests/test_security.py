import io

from app import ratelimit


def _post(client, text, **kw):
    return client.post("/api/analyze", json={"role": "sde", "text": text}, **kw)


def test_rate_limit_returns_429(client, sample_text):
    client.application.config["RATE_LIMIT_PER_MIN"] = 3
    ratelimit.reset()
    codes = [_post(client, sample_text).status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200] and codes[3:] == [429, 429]
    assert _post(client, sample_text).headers["Retry-After"]


def test_fake_pdf_rejected(client):
    data = {"role": "sde", "file": (io.BytesIO(b"not really a pdf"), "resume.pdf")}
    r = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert r.status_code == 400 and "valid PDF" in r.json["error"]


def test_fake_docx_rejected(client):
    data = {"role": "sde", "file": (io.BytesIO(b"plain text"), "resume.docx")}
    r = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert r.status_code == 400


def test_binary_txt_rejected(client):
    data = {"role": "sde", "file": (io.BytesIO(b"abc\x00def"), "resume.txt")}
    r = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert r.status_code == 400


def test_oversize_upload_returns_413(client):
    client.application.config["MAX_CONTENT_LENGTH"] = 1000
    data = {"role": "sde", "file": (io.BytesIO(b"a" * 5000), "resume.txt")}
    assert client.post("/api/analyze", data=data, content_type="multipart/form-data").status_code == 413


def test_security_headers(client):
    r = client.get("/api/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"


def test_stats_endpoint(client, sample_text):
    _post(client, sample_text)
    stats = client.get("/api/stats").json
    assert stats["total_analyses"] == 1 and "sde" in stats["by_role"]
