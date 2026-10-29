from fastapi.testclient import TestClient

from app import app
from tutor import profiles

client = TestClient(app)


def test_index_page_is_served():
    response = client.get("/")

    assert response.status_code == 200
    assert '<script src="app.js">' in response.text


def test_api_routes_win_over_static_files(tmp_path, monkeypatch):
    monkeypatch.setattr(profiles, "PROFILES_DIR", tmp_path)

    assert client.get("/api/profiles").json() == []
