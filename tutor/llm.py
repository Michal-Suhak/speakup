import logging
import time
from contextlib import contextmanager
from functools import lru_cache
from string import Template
from typing import Iterator, TypeVar

from openai import OpenAI, OpenAIError
from pydantic import ValidationError

import config
from tutor.schemas import Correction, Summary, TutorTurn

MAX_VISIBLE_CORRECTIONS = 3
from tutor.session import Message, Session, Usage

log = logging.getLogger(__name__)
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
SUMMARY_INSTRUCTION = "The session has ended. Write the summary of the whole conversation above."
Answer = TypeVar("Answer", TutorTurn, Summary)


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


def render_summary_prompt(session: Session) -> str:
    profile = session.profile
    template = Template((PROMPTS_DIR / "summary.md").read_text(encoding="utf-8"))
    return template.substitute(name=profile.name, level=profile.level, topic=session.topic)


@contextmanager
def timed(step: str, model: str) -> Iterator[None]:
    started = time.perf_counter()
    try:
        yield
    finally:
        log.info("%s took %.2f s (%s)", step, time.perf_counter() - started, model)


@lru_cache
def get_client() -> OpenAI:
    if not config.OPENAI_API_KEY:
        raise LLMUnavailable("OPENAI_API_KEY is missing. Copy env.example to .env, set your key and restart.")
    return OpenAI(api_key=config.OPENAI_API_KEY, timeout=REQUEST_TIMEOUT_SECONDS, max_retries=1)


def _ask(instructions: str, messages: list[Message], usage: Usage, text_format: type[Answer] = TutorTurn) -> Answer:
    for _ in range(PARSE_ATTEMPTS):
        try:
            with timed("LLM", config.CHAT_MODEL):
                response = get_client().responses.parse(
                    model=config.CHAT_MODEL,
                    instructions=instructions,
                    input=[{"role": m.role, "content": m.content} for m in messages],
                    text_format=text_format,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                )
        except OpenAIError as error:
            raise LLMError(f"OpenAI request failed ({type(error).__name__}). Try again in a moment.") from error
        except ValidationError:
            continue
        if response.usage:
            usage.chat_input_tokens += response.usage.input_tokens
            usage.chat_output_tokens += response.usage.output_tokens
        if response.output_parsed is not None:
            return response.output_parsed
    raise LLMError("The tutor did not return a valid answer. Try again.")


def visible_corrections(turn: TutorTurn, user_text: str, correction_style: str) -> list[Correction]:
    said = user_text.casefold()
    shown = [
        c
        for c in turn.corrections
        if c.you_said.strip().casefold() in said and (correction_style == "strict" or c.severity == "important")
    ]
    shown.sort(key=lambda c: c.severity != "important")
    return shown[:MAX_VISIBLE_CORRECTIONS]


def start(session: Session) -> TutorTurn:
    with session.turn():
        turn = _ask(render_system_prompt(session), [Message("user", START_INSTRUCTION)], session.usage)
        turn.corrections = []
        session.messages.append(Message("assistant", turn.reply))
        return turn


def reply(session: Session, user_text: str) -> TutorTurn:
    with session.turn():
        message = Message("user", user_text)
        history = [*session.messages, message][-MAX_HISTORY_MESSAGES:]
        turn = _ask(render_system_prompt(session), history, session.usage)
        turn.corrections = visible_corrections(turn, user_text, session.profile.correction_style)
        session.messages += [message, Message("assistant", turn.reply)]
        return turn


def summarize(session: Session) -> Summary | None:
    """Feedback on the whole session, or None when the learner never answered."""
    with session.turn():
        said = [m.content.casefold() for m in session.messages if m.role == "user"]
        if not said:
            return None
        summary = _ask(render_summary_prompt(session), [*session.messages, Message("user", SUMMARY_INSTRUCTION)], session.usage, Summary)
        summary.top_corrections = [
            c for c in summary.top_corrections if any(c.you_said.strip().casefold() in text for text in said)
        ]
        return summary
