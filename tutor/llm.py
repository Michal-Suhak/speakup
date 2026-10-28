from functools import lru_cache
from string import Template

from openai import APIError, OpenAI
from pydantic import BaseModel, Field, ValidationError

import config
from tutor.session import Message, Session

PROMPTS_DIR = config.BASE_DIR / "prompts"
# ponytail: plain sliding window; summarise older turns if long sessions lose context
MAX_HISTORY_MESSAGES = 40
START_INSTRUCTION = (
    "Start the session: greet the learner by name in one short sentence "
    "and ask your first question about the session topic."
)


class LLMUnavailable(Exception):
    pass


class LLMError(Exception):
    pass


class Correction(BaseModel):
    you_said: str = Field(description="The learner's exact words that contain the mistake.")
    better: str = Field(description="The corrected version of those words.")
    explanation_pl: str = Field(description="One short sentence in Polish explaining the correction.")


class TutorTurn(BaseModel):
    corrections: list[Correction] = Field(
        description="Mistakes from the learner's last message only. Empty when there is nothing to correct."
    )
    reply: str = Field(description="The tutor's spoken reply in English: 2-4 sentences, plain text.")


def _join(values: list[str]) -> str:
    return ", ".join(values) or "none"


def render_system_prompt(session: Session) -> str:
    profile = session.profile
    template = Template((PROMPTS_DIR / "tutor.md").read_text(encoding="utf-8"))
    return template.substitute(
        topic=session.topic,
        level=profile.level,
        name=profile.name,
        interests=_join(profile.interests),
        goals=profile.goals or "none",
        avoid_topics=_join(profile.avoid_topics),
        correction_style=profile.correction_style,
    )


@lru_cache
def get_client() -> OpenAI:
    if not config.OPENAI_API_KEY:
        raise LLMUnavailable("OPENAI_API_KEY is missing. Copy env.example to .env, set your key and restart.")
    return OpenAI(api_key=config.OPENAI_API_KEY)


def _ask(instructions: str, messages: list[Message]) -> TutorTurn:
    try:
        response = get_client().responses.parse(
            model=config.CHAT_MODEL,
            instructions=instructions,
            input=[{"role": m.role, "content": m.content} for m in messages],
            text_format=TutorTurn,
        )
    except APIError as error:
        raise LLMError(f"OpenAI request failed ({type(error).__name__}). Try again in a moment.") from error
    except ValidationError as error:
        raise LLMError("The tutor returned an invalid answer. Try again.") from error
    if response.output_parsed is None:
        raise LLMError("The tutor did not return an answer. Try again.")
    return response.output_parsed


def start(session: Session) -> TutorTurn:
    with session.turn():
        turn = _ask(render_system_prompt(session), [Message("user", START_INSTRUCTION)])
        session.messages.append(Message("assistant", turn.reply))
        return turn


def reply(session: Session, user_text: str) -> TutorTurn:
    with session.turn():
        message = Message("user", user_text)
        history = [*session.messages, message][-MAX_HISTORY_MESSAGES:]
        turn = _ask(render_system_prompt(session), history)
        session.messages += [message, Message("assistant", turn.reply)]
        return turn
