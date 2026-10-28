from functools import lru_cache
from string import Template

from openai import APIError, OpenAI
from pydantic import ValidationError

import config
from tutor.schemas import Correction, TutorTurn
from tutor.session import Message, Session

PROMPTS_DIR = config.BASE_DIR / "prompts"
# ponytail: plain sliding window; summarise older turns if long sessions lose context
MAX_HISTORY_MESSAGES = 40
REQUEST_TIMEOUT_SECONDS = 30
MAX_OUTPUT_TOKENS = 2000
PARSE_ATTEMPTS = 2
START_INSTRUCTION = (
    "Start the session: greet the learner by name in one short sentence "
    "and ask your first question about the session topic."
)


class LLMUnavailable(Exception):
    pass


class LLMError(Exception):
    pass


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
    return OpenAI(api_key=config.OPENAI_API_KEY, timeout=REQUEST_TIMEOUT_SECONDS, max_retries=1)


def _ask(instructions: str, messages: list[Message]) -> TutorTurn:
    for _ in range(PARSE_ATTEMPTS):
        try:
            response = get_client().responses.parse(
                model=config.CHAT_MODEL,
                instructions=instructions,
                input=[{"role": m.role, "content": m.content} for m in messages],
                text_format=TutorTurn,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            )
        except APIError as error:
            raise LLMError(f"OpenAI request failed ({type(error).__name__}). Try again in a moment.") from error
        except ValidationError:
            continue
        if response.output_parsed is not None:
            return response.output_parsed
    raise LLMError("The tutor did not return a valid answer. Try again.")


def visible_corrections(turn: TutorTurn, user_text: str, correction_style: str) -> list[Correction]:
    said = user_text.casefold()
    return [
        c
        for c in turn.corrections
        if c.you_said.strip().casefold() in said and (correction_style == "strict" or c.severity == "important")
    ]


def start(session: Session) -> TutorTurn:
    with session.turn():
        turn = _ask(render_system_prompt(session), [Message("user", START_INSTRUCTION)])
        turn.corrections = []
        session.messages.append(Message("assistant", turn.reply))
        return turn


def reply(session: Session, user_text: str) -> TutorTurn:
    with session.turn():
        message = Message("user", user_text)
        history = [*session.messages, message][-MAX_HISTORY_MESSAGES:]
        turn = _ask(render_system_prompt(session), history)
        turn.corrections = visible_corrections(turn, user_text, session.profile.correction_style)
        session.messages += [message, Message("assistant", turn.reply)]
        return turn
