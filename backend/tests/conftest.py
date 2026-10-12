import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402


@pytest.fixture()
def client(tmp_path):
    from app import ratelimit
    ratelimit.reset()
    app = create_app(database_url=f"sqlite:///{tmp_path/'test.db'}")
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture()
def sample_text():
    return (Path(__file__).parent / "data" / "sample_resume.txt").read_text()
