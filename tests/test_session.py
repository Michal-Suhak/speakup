import logging
import threading

import pytest

from tutor import session
from tutor.profiles import Profile
from tutor.session import SESSION_IDLE_MINUTES, Session, SessionNotFound, get_session, register_session

IDLE_SECONDS = SESSION_IDLE_MINUTES * 60


@pytest.fixture(autouse=True)
def no_sessions(monkeypatch):
    monkeypatch.setattr(session, "_sessions", {})


def new_session():
    created = Session(profile=Profile(id="michal", name="Michał"), topic="Travel")
    register_session(created)
    return created


def test_idle_session_expires_and_is_logged(caplog):
    idle = new_session()
    idle.usage.chat_output_tokens = 1000
    idle.last_active -= IDLE_SECONDS + 1

    with caplog.at_level(logging.INFO, logger="tutor"):
        with pytest.raises(SessionNotFound):
            get_session(idle.id)

    assert [r.getMessage() for r in caplog.records] == [
        f"Session {idle.id} expired after 30 min idle: 0.0005 USD, "
        "{'chat_input_tokens': 0, 'chat_output_tokens': 1000, 'stt_input_tokens': 0, 'stt_output_tokens': 0, 'tts_characters': 0}"
    ]


def test_turn_keeps_the_session_alive():
    active = new_session()
    active.last_active -= IDLE_SECONDS + 1
    with active.turn():
        pass

    assert get_session(active.id) is active


def test_busy_session_is_never_expired():
    busy = new_session()
    started, release = threading.Event(), threading.Event()

    def hold_turn():
        with busy.turn():
            busy.last_active -= IDLE_SECONDS + 1
            started.set()
            release.wait()

    worker = threading.Thread(target=hold_turn)
    worker.start()
    started.wait()
    new_session()
    assert session._sessions[busy.id] is busy
    release.set()
    worker.join()
