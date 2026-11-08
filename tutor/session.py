import logging
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from typing import Iterator, Literal

import config
from tutor.profiles import Profile

log = logging.getLogger(__name__)
SESSION_IDLE_MINUTES = 30


class SessionNotFound(Exception):
    pass


class SessionBusy(Exception):
    pass


@dataclass
class Message:
    role: Literal["user", "assistant"]
    content: str


@dataclass
class Usage:
    chat_input_tokens: int = 0
    chat_output_tokens: int = 0
    stt_input_tokens: int = 0
    stt_output_tokens: int = 0
    tts_characters: int = 0

    def cost_usd(self) -> float:
        per_token = (
            self.chat_input_tokens * config.CHAT_INPUT_USD_PER_1M_TOKENS
            + self.chat_output_tokens * config.CHAT_OUTPUT_USD_PER_1M_TOKENS
            + self.stt_input_tokens * config.STT_INPUT_USD_PER_1M_TOKENS
            + self.stt_output_tokens * config.STT_OUTPUT_USD_PER_1M_TOKENS
            + self.tts_characters * config.TTS_USD_PER_1M_CHARACTERS
        )
        return per_token / 1_000_000


@dataclass
class Session:
    profile: Profile
    topic: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    messages: list[Message] = field(default_factory=list)
    started: float = field(default_factory=time.monotonic)
    usage: Usage = field(default_factory=Usage)
    last_active: float = field(default_factory=time.monotonic)
    # reentrant, so a voice turn can hold the lock through transcription and the reply in one request
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    @contextmanager
    def turn(self) -> Iterator[None]:
        if not self._lock.acquire(blocking=False):
            raise SessionBusy("The tutor is still answering the previous message.")
        self.last_active = time.monotonic()
        try:
            yield
        finally:
            self.last_active = time.monotonic()
            self._lock.release()


_sessions: dict[str, Session] = {}


def expire_idle_sessions() -> None:
    """Remove sessions idle for longer than SESSION_IDLE_MINUTES, e.g. when the browser never sent the end call."""
    now = time.monotonic()
    for session in list(_sessions.values()):
        idle_minutes = (now - session.last_active) / 60
        if idle_minutes <= SESSION_IDLE_MINUTES or not session._lock.acquire(blocking=False):
            continue
        try:
            _sessions.pop(session.id, None)
        finally:
            session._lock.release()
        log.info(
            "Session %s expired after %d min idle: %.4f USD, %s",
            session.id,
            idle_minutes,
            session.usage.cost_usd(),
            asdict(session.usage),
        )


def register_session(session: Session) -> None:
    expire_idle_sessions()
    _sessions[session.id] = session


def get_session(session_id: str) -> Session:
    expire_idle_sessions()
    session = _sessions.get(session_id)
    if session is None:
        raise SessionNotFound("Session not found. Start a new session.")
    return session


def remove_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
