import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import app
from tutor import profiles
from tutor.profiles import DEFAULT_INTERESTS, Profile


@pytest.fixture
def profiles_dir(tmp_path, monkeypatch):
    directory = tmp_path / "profiles"
    monkeypatch.setattr(profiles, "PROFILES_DIR", directory)
    return directory


@pytest.fixture
def client(profiles_dir):
    return TestClient(app)


def put(client, profile_id, **fields):
    return client.put(f"/api/profiles/{profile_id}", json={"id": profile_id, **fields})


def test_new_profile_gets_defaults():
    profile = Profile(id="michal", name="Michał")
    assert profile.level == "B1"
    assert profile.interests == DEFAULT_INTERESTS
    assert profile.avoid_topics == []
    assert profile.correction_style == "gentle"


@pytest.mark.parametrize(
    "fields",
    [
        {"id": "../x"},
        {"level": "D1"},
        {"goals": "a" * 301},
        {"name": ""},
        {"interests": ["t"] * 21},
        {"avoid_topics": ["a" * 41]},
        {"correction_style": "harsh"},
    ],
)
def test_profile_rejects_invalid_fields(fields):
    with pytest.raises(ValidationError):
        Profile(**{"id": "x", "name": "X", **fields})


def test_empty_list(client):
    assert client.get("/api/profiles").json() == []


def test_save_and_load(client, profiles_dir):
    saved = put(client, "michal", name="Michał")
    assert saved.status_code == 200

    assert client.get("/api/profiles/michal").json() == saved.json()
    assert client.get("/api/profiles").json() == [{"id": "michal", "name": "Michał", "level": "B1"}]
    assert "Michał" in (profiles_dir / "michal.json").read_text(encoding="utf-8")
    assert not list(profiles_dir.glob("*.tmp"))


def test_missing_profile_is_404(client):
    assert client.get("/api/profiles/nobody").status_code == 404


@pytest.mark.parametrize("bad_id", ["Michal", "a" * 33, "a.b", "-%2e%2e"])
def test_invalid_id_is_400(client, bad_id):
    assert client.get(f"/api/profiles/{bad_id}").status_code == 400


def test_traversal_never_touches_files(client, tmp_path):
    response = client.put("/api/profiles/..%2F.env", json={"id": "x", "name": "X"})
    assert response.status_code in (400, 404, 405)
    assert not (tmp_path / ".env").exists()


def test_id_mismatch_is_400(client):
    response = client.put("/api/profiles/abc", json={"id": "other", "name": "X"})
    assert response.status_code == 400


def test_invalid_field_is_422(client):
    assert put(client, "abc", name="X", level="Z9").status_code == 422


@pytest.mark.parametrize(
    ("file_name", "content"),
    [
        ("broken.json", b"{not json"),
        ("latin.json", '{"id": "latin", "name": "Michał"}'.encode("cp1250")),
        ("kasia.json", b'{"id": "michal", "name": "Michal"}'),
    ],
)
def test_broken_file_is_skipped_and_reported(client, profiles_dir, file_name, content):
    put(client, "michal", name="Michał")
    (profiles_dir / file_name).write_bytes(content)

    assert [p["id"] for p in client.get("/api/profiles").json()] == ["michal"]

    response = client.get(f"/api/profiles/{file_name.removesuffix('.json')}")
    assert response.status_code == 400
    assert "Fix or delete the file" in response.json()["detail"]
