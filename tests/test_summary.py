import threading

import pytest
from fastapi.testclient import TestClient

from app import app
from tutor import llm, profiles, session
from tutor.llm import LLMError
from tutor.profiles import Profile, save_profile
from tutor.schemas import Summary, SummaryCorrection, TutorTurn, Vocabulary
from tutor.session import Session

SUMMARY = Summary(
    top_corrections=[SummaryCorrection(you_said="I go", better="I went", explanation_pl="Czas przeszły.")],
    useful_vocabulary=[Vocabulary(word="sightseeing", meaning_pl="zwiedzanie", example="We went sightseeing.")],
    strengths=["Mówisz pełnymi zdaniami."],
    tip_pl="Ćwicz czas przeszły.",
)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(profiles, "PROFILES_DIR", tmp_path / "profiles")
    monkeypatch.setattr(session, "_sessions", {})
    save_profile(Profile(id="michal", name="Michał", level="A2"))


@pytest.fixture
def calls(monkeypatch):
    recorded = []

    def fake_ask(instructions, messages, text_format=TutorTurn):
        recorded.append((instructions, list(messages), text_format))
        if text_format is Summary:
            return SUMMARY
        return TutorTurn(analysis="", corrections=[], reply="Where?")

    monkeypatch.setattr(llm, "_ask", fake_ask)
    return recorded


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def session_id(client, calls):
    return client.post("/api/session", json={"profile_id": "michal", "topic": "Travel"}).json()["session_id"]


def end(client, session_id):
    return client.post(f"/api/session/{session_id}/end")


def test_summary_of_the_whole_session(client, session_id, calls):
    client.post("/api/text", json={"session_id": session_id, "text": "I go to Rome"})
    response = end(client, session_id)

    assert response.status_code == 200
    assert response.json()["summary"] == SUMMARY.model_dump()
    assert isinstance(response.json()["duration_seconds"], int)
    instructions, messages, text_format = calls[-1]
    assert text_format is Summary
    assert "Session topic: Travel" in instructions
    assert [m.content for m in messages[:-1]] == ["Where?", "I go to Rome", "Where?"]
    assert messages[-1].content == llm.SUMMARY_INSTRUCTION
    assert client.post("/api/text", json={"session_id": session_id, "text": "Hi"}).status_code == 404


def test_session_without_answers_has_no_summary(client, session_id, calls):
    response = end(client, session_id)

    assert response.status_code == 200
    assert response.json()["summary"] is None
    assert len(calls) == 1


def test_failed_summary_keeps_the_session(client, session_id, calls, monkeypatch):
    client.post("/api/text", json={"session_id": session_id, "text": "Hi"})

    def failing(*args):
        raise LLMError("The tutor did not return a valid answer. Try again.")

    monkeypatch.setattr(llm, "_ask", failing)
    assert end(client, session_id).status_code == 502
    assert session.get_session(session_id)


def test_end_while_answering_is_409(client, session_id):
    with session.get_session(session_id).turn():
        result = {}
        worker = threading.Thread(target=lambda: result.setdefault("response", end(client, session_id)))
        worker.start()
        worker.join()

    assert result["response"].status_code == 409


def test_unknown_session_is_404(client, calls):
    assert end(client, "missing").status_code == 404


def test_summary_prompt_keeps_profile_as_data():
    profile = Profile(id="kasia", name="Kasia {x}", level="B2")
    prompt = llm.render_summary_prompt(Session(profile=profile, topic="Food $5"))

    assert "$" not in prompt.replace("$5", "")
    assert prompt.index("<learner_profile>") < prompt.index("Name: Kasia {x}") < prompt.index("</learner_profile>")
    assert "CEFR level B2" in prompt
