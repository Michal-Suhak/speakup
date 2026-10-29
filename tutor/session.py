import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator, Literal

from tutor.profiles import Profile


class SessionNotFound(Exception):
    pass


class SessionBusy(Exception):
    pass


@dataclass
class Message:
    role: Literal["user", "assistant"]
    content: str


@dataclass
class Session:
    profile: Profile
    topic: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    messages: list[Message] = field(default_factory=list)
    started: float = field(default_factory=time.monotonic)
    # reentrant, so a voice turn can hold the lock through transcription and the reply in one request
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    @contextmanager
    def turn(self) -> Iterator[None]:
        if not self._lock.acquire(blocking=False):
            raise SessionBusy("The tutor is still answering the previous message.")
        try:
            yield
        finally:
            self._lock.release()


_sessions: dict[str, Session] = {}


# ponytail: sessions that are never ended stay until the server stops
def register_session(session: Session) -> None:
    _sessions[session.id] = session


def get_session(session_id: str) -> Session:
    session = _sessions.get(session_id)
    if session is None:
        raise SessionNotFound("Session not found. Start a new session.")
    return session


def remove_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
