import base64
import logging
import time
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field, StringConstraints

from tutor import llm, stt, tts
from tutor.profiles import load_profile
from tutor.schemas import Summary, TutorTurn
from tutor.session import Session, get_session, register_session, remove_session

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["sessions"])

Topic = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
UserText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class StartRequest(BaseModel):
    """Start a session: the tutor greets the learner and asks the first question."""

    profile_id: str = Field(examples=["michal"])
    topic: Topic = Field(description="Topic of the conversation, 1-80 characters.", examples=["Travel"])


class StartResponse(BaseModel):
    session_id: str = Field(description="Send it with every message of this session.")
    reply: str = Field(description="The tutor's greeting, in English.", examples=["Hi Michał! Where did you travel last?"])
    audio: str | None = Field(None, description="The reply as base64 mp3; missing when speech synthesis failed.")


class TextRequest(BaseModel):
    """One learner message in a running session."""

    session_id: str
    text: UserText = Field(description="The learner's message, 1-1000 characters.", examples=["I go to Spain last summer."])


class CorrectionOut(BaseModel):
    """One mistake from the learner's message."""

    you_said: str = Field(description="Fragment of the learner's message with the mistake.", examples=["I go to Spain"])
    better: str = Field(description="The corrected fragment.", examples=["I went to Spain"])
    explanation_pl: str = Field(
        description="Short explanation in Polish.", examples=["Mówimy o przeszłości, więc używamy formy „went”."]
    )


class TurnResponse(BaseModel):
    """The tutor's answer to one learner message."""

    reply: str = Field(description="What the tutor says, in English.", examples=["Oh, you went to Spain? Nice! What did you see?"])
    corrections: list[CorrectionOut] = Field(description="Mistakes to show the learner; may be empty.")
    audio: str | None = Field(None, description="The reply as base64 mp3; missing when speech synthesis failed.")


class VoiceTurnResponse(TurnResponse):
    """The tutor's answer to one spoken learner message."""

    user_text: str = Field(description="What the learner said, as transcribed.", examples=["I go to Spain last summer."])


class EndResponse(BaseModel):
    summary: Summary | None = Field(description="Feedback on the session; null when the learner never answered or no summary was asked for.")
    duration_seconds: int = Field(description="Time from the start of the session to its end.")
    usage: dict[str, int] = Field(description="Tokens and characters used by the session, including the summary.")
    cost_usd: float = Field(description="Approximate cost of the session in USD, from the rates in config.py.")


def _turn_fields(turn: TutorTurn) -> dict:
    return TurnResponse.model_validate(turn, from_attributes=True).model_dump(exclude={"audio"})


def speak(session: Session, text: str) -> str | None:
    audio = tts.synthesize(text, session.profile.level, session.usage)
    return base64.b64encode(audio).decode("ascii") if audio else None


@router.post("/session")
def start_session(request: StartRequest) -> StartResponse:
    profile = load_profile(request.profile_id)
    if profile is None:
        raise HTTPException(404, "Profile not found.")
    session = Session(profile=profile, topic=request.topic)
    turn = llm.start(session)
    reply_audio = speak(session, turn.reply)
    register_session(session)
    return StartResponse(session_id=session.id, reply=turn.reply, audio=reply_audio)


@router.post("/text")
def text_turn(request: TextRequest) -> TurnResponse:
    session = get_session(request.session_id)
    with session.turn():
        turn = llm.reply(session, request.text)
        reply_audio = speak(session, turn.reply)
    return TurnResponse(**_turn_fields(turn), audio=reply_audio)


@router.post("/turn")
def voice_turn(session_id: Annotated[str, Form()], audio: UploadFile) -> VoiceTurnResponse:
    session = get_session(session_id)
    with session.turn():
        data = audio.file.read(stt.MAX_AUDIO_BYTES + 1)
        user_text = stt.transcribe(data, audio.filename or "", session.usage)
        turn = llm.reply(session, user_text)
        reply_audio = speak(session, turn.reply)
    return VoiceTurnResponse(user_text=user_text, **_turn_fields(turn), audio=reply_audio)


@router.post("/session/{session_id}/end")
def end_session(session_id: str, summary: bool = True) -> EndResponse:
    """End a session; with `summary=false` (leaving without feedback) it only reports usage and cost."""
    session = get_session(session_id)
    with session.turn():
        feedback = llm.summarize(session) if summary else None
        remove_session(session_id)
    log.info("Session %s ended: %.4f USD, %s", session.id, session.usage.cost_usd(), asdict(session.usage))
    return EndResponse(
        summary=feedback,
        duration_seconds=round(time.monotonic() - session.started),
        usage=asdict(session.usage),
        cost_usd=round(session.usage.cost_usd(), 6),
    )
