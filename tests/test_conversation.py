import threading

import pytest
from fastapi.testclient import TestClient

from app import app
from tutor import llm, profiles, session
from tutor.llm import Correction, LLMError, LLMUnavailable, TutorTurn
from tutor.profiles import Profile, save_profile
from tutor.session import Message, Session


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(profiles, "PROFILES_DIR", tmp_path / "profiles")
    monkeypatch.setattr(session, "_sessions", {})
    save_profile(
        Profile(
            id="michal",
            name="Michał",
            level="A2",
            interests=["football", "travel"],
            avoid_topics=["politics"],
            correction_style="strict",
        )
    )


@pytest.fixture
def calls(monkeypatch):
    recorded = []

    def fake_ask(instructions, messages):
        recorded.append((instructions, list(messages)))
        corrections = []
        if messages[-1].content == "I go there yesterday":
            corrections = [Correction(you_said="I go", better="I went", explanation_pl="Czas przeszły.")]
        return TutorTurn(corrections=corrections, reply=f"Reply {len(recorded)}?")

    monkeypatch.setattr(llm, "_ask", fake_ask)
    return recorded


@pytest.fixture
def client():
    return TestClient(app)


def start(client, topic="Football"):
    return client.post("/api/session", json={"profile_id": "michal", "topic": topic})


def test_prompt_uses_profile_and_keeps_braces():
    profile = Profile(id="kasia", name="Kasia", goals="", avoid_topics=[], interests=[])
    prompt = llm.render_system_prompt(Session(profile=profile, topic="Food {and} $5 drinks"))

    assert "$" not in prompt.replace("$5", "")
    assert "Session topic: Food {and} $5 drinks" in prompt
    assert "Goals: none" in prompt
    assert "Topics to avoid: none" in prompt
    assert "Correction style: gentle" in prompt
    assert prompt.index("<learner_profile>") < prompt.index("Name: Kasia") < prompt.index("</learner_profile>")


def test_prompt_joins_lists():
    profile = profiles.load_profile("michal")
    prompt = llm.render_system_prompt(Session(profile=profile, topic="Travel"))
    assert "Interests: football, travel" in prompt
    assert "CEFR level A2" in prompt


def test_start_and_text_turn(client, calls):
    started = start(client)
    assert started.status_code == 200
    session_id = started.json()["session_id"]
    assert started.json()["reply"] == "Reply 1?"

    first_instructions, first_messages = calls[0]
    assert "Session topic: Football" in first_instructions
    assert [m.role for m in first_messages] == ["user"]

    turn = client.post("/api/text", json={"session_id": session_id, "text": "I go there yesterday"})
    assert turn.status_code == 200
    assert turn.json() == {
        "corrections": [{"you_said": "I go", "better": "I went", "explanation_pl": "Czas przeszły."}],
        "reply": "Reply 2?",
    }

    _, history = calls[1]
    assert [(m.role, m.content) for m in history] == [
        ("assistant", "Reply 1?"),
        ("user", "I go there yesterday"),
    ]

    stored = session.get_session(session_id).messages
    assert [m.content for m in stored] == ["Reply 1?", "I go there yesterday", "Reply 2?"]


def test_history_is_trimmed(client, calls, monkeypatch):
    monkeypatch.setattr(llm, "MAX_HISTORY_MESSAGES", 4)
    session_id = start(client).json()["session_id"]
    for i in range(5):
        client.post("/api/text", json={"session_id": session_id, "text": f"message {i}"})

    _, history = calls[-1]
    assert len(history) == 4
    assert history[-1] == Message("user", "message 4")


def test_unknown_profile_is_404(client, calls):
    response = client.post("/api/session", json={"profile_id": "nobody", "topic": "Food"})
    assert response.status_code == 404
    assert calls == []


def test_unknown_session_is_404(client, calls):
    response = client.post("/api/text", json={"session_id": "missing", "text": "Hi"})
    assert response.status_code == 404


@pytest.mark.parametrize(
    "body",
    [
        {"profile_id": "michal", "topic": ""},
        {"profile_id": "michal", "topic": "   "},
        {"profile_id": "michal", "topic": "t" * 81},
    ],
)
def test_invalid_topic_is_422(client, calls, body):
    assert client.post("/api/session", json=body).status_code == 422


@pytest.mark.parametrize("text", ["", "   ", "a" * 1001])
def test_invalid_text_is_422(client, calls, text):
    session_id = start(client).json()["session_id"]
    assert client.post("/api/text", json={"session_id": session_id, "text": text}).status_code == 422


def test_parallel_turn_is_409(client, monkeypatch):
    entered, release = threading.Event(), threading.Event()

    def slow_ask(instructions, messages):
        if len(messages) > 1:
            entered.set()
            release.wait(5)
        return TutorTurn(corrections=[], reply="Hi?")

    monkeypatch.setattr(llm, "_ask", slow_ask)
    session_id = start(client).json()["session_id"]

    worker = threading.Thread(target=client.post, args=("/api/text",), kwargs={"json": {"session_id": session_id, "text": "one"}})
    worker.start()
    assert entered.wait(5)
    second = client.post("/api/text", json={"session_id": session_id, "text": "two"})
    release.set()
    worker.join()

    assert second.status_code == 409
    assert [m.content for m in session.get_session(session_id).messages] == ["Hi?", "one", "Hi?"]


@pytest.mark.parametrize(
    ("error", "status"),
    [(LLMError("OpenAI request failed."), 502), (LLMUnavailable("OPENAI_API_KEY is missing."), 503)],
)
def test_llm_errors_are_readable(client, monkeypatch, error, status):
    def failing_ask(instructions, messages):
        raise error

    monkeypatch.setattr(llm, "_ask", failing_ask)
    response = start(client)
    assert response.status_code == status
    assert response.json() == {"detail": str(error)}


def test_missing_key_raises_unavailable(monkeypatch):
    llm.get_client.cache_clear()
    monkeypatch.setattr(llm.config, "OPENAI_API_KEY", "")
    with pytest.raises(LLMUnavailable):
        llm.get_client()
    llm.get_client.cache_clear()
