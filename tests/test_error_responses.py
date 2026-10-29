import pytest
from fastapi.testclient import TestClient

from app import app
from tutor import profiles

SECRET = "PRIVATE-GOAL-TEXT"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(profiles, "PROFILES_DIR", tmp_path / "profiles")
    return TestClient(app)


@pytest.mark.parametrize(
    "body",
    [
        {"id": "abc", "name": "X", "goals": SECRET * 30},
        {"id": "abc", "name": "X", "correction_style": SECRET},
        {"id": "abc", "name": "X", "interests": [SECRET * 5]},
    ],
)
def test_validation_errors_do_not_echo_input(client, body):
    response = client.put("/api/profiles/abc", json=body)

    assert response.status_code == 422
    assert SECRET not in response.text
    error = response.json()["detail"][0]
    assert set(error) == {"loc", "msg", "type"}
    assert error["loc"][0] == "body"
