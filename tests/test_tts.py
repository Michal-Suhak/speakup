import base64
import threading
from types import SimpleNamespace

import openai
import pytest
from fastapi.testclient import TestClient

from app import app
from tutor import llm, profiles, session
from tutor.profiles import Profile, save_profile
from tutor.schemas import TutorTurn


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(profiles, "PROFILES_DIR", tmp_path / "profiles")
    monkeypatch.setattr(session, "_sessions", {})
    save_profile(Profile(id="michal", name="Michał", level="A2"))
    monkeypatch.setattr(llm, "_ask", lambda instructions, messages, *_: TutorTurn(analysis="", corrections=[], reply="Hi there?", reply_pl="Po polsku."))


@pytest.fixture
def client():
    return TestClient(app)


def test_replies_come_with_audio(client, speech):
    started = client.post("/api/session", json={"profile_id": "michal", "topic": "Travel"}).json()
    answered = client.post("/api/text", json={"session_id": started["session_id"], "text": "Hello"}).json()

    assert base64.b64decode(started["audio"]) == speech.content
    assert base64.b64decode(answered["audio"]) == speech.content
    sent = speech.calls[-1]
    assert sent["input"] == "Hi there?"
    assert "level A2" in sent["instructions"]
    assert "$" not in sent["instructions"]


def test_session_stays_locked_while_the_reply_is_spoken(client, speech, monkeypatch):
    session_id = client.post("/api/session", json={"profile_id": "michal", "topic": "Travel"}).json()["session_id"]
    statuses = []

    def end_from_another_client(**kwargs):
        worker = threading.Thread(target=lambda: statuses.append(client.post(f"/api/session/{session_id}/end").status_code))
        worker.start()
        worker.join()
        return SimpleNamespace(content=speech.content)

    monkeypatch.setattr(speech, "create", end_from_another_client)
    assert client.post("/api/text", json={"session_id": session_id, "text": "Hello"}).status_code == 200
    assert statuses == [409]


def test_tts_failure_keeps_the_text_reply(client, speech):
    speech.error = openai.OpenAIError("secret provider detail")
    response = client.post("/api/session", json={"profile_id": "michal", "topic": "Travel"})

    assert response.status_code == 200
    assert response.json()["reply"] == "Hi there?"
    assert response.json()["audio"] is None
    assert "secret provider detail" not in response.text
