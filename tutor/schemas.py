from typing import Annotated, Literal

from annotated_types import MaxLen
from pydantic import BaseModel, Field

MAX_CORRECTIONS = 5


class Correction(BaseModel):
    """One mistake from the learner's last message, with its fix and a short Polish explanation."""

    you_said: str = Field(
        description=(
            "The exact fragment of the learner's last message that contains the mistake, copied character for "
            "character (2-8 words, enough context to recognise it). Never paraphrase and never quote the tutor. "
            "Example: 'Last summer I go to Spain'."
        )
    )
    better: str = Field(
        description=(
            "The same fragment rewritten the way a native speaker would say it at the learner's level. "
            "Change only what is wrong and keep the rest of the words. Example: 'Last summer I went to Spain'."
        )
    )
    mistake_type: Literal["grammar", "word_choice", "polish_word", "word_order"] = Field(
        description=(
            "Kind of mistake: "
            "grammar = tense, verb form, subject-verb agreement, articles, prepositions, plurals; "
            "word_choice = an English word that is wrong or unnatural in this context; "
            "polish_word = a Polish word used instead of an English one; "
            "word_order = correct words in the wrong order."
        )
    )
    severity: Literal["important", "minor"] = Field(
        description=(
            "important = changes or hides the meaning, uses a Polish word, or breaks a basic rule the learner "
            "should know at their level (e.g. past tense, he/she + s, was/were); "
            "minor = a small slip that does not affect understanding (e.g. a missing article or a wrong "
            "preposition). Judge by impact on understanding, not by how easy the fix is."
        )
    )
    explanation_pl: str = Field(
        description=(
            "One short sentence in Polish (at most 15 words) that says why the fix is needed, naming the rule "
            "in plain words. Example: 'Mówimy o przeszłości, więc używamy formy „went”.'"
        )
    )


class TutorTurn(BaseModel):
    """The tutor's answer to the learner's last message. Fill the fields in order: analysis, corrections, reply, reply_pl."""

    analysis: str = Field(
        description=(
            "Working notes, not shown to the learner: 1-2 short sentences in English about what the learner "
            "meant and which mistakes the message contains. At the start of a session write 'Session start'."
        )
    )
    corrections: Annotated[list[Correction], MaxLen(MAX_CORRECTIONS)] = Field(
        description=(
            f"Every real language mistake in the learner's last message, at most {MAX_CORRECTIONS}: all important "
            "ones first, then minor ones. List minor mistakes too and mark them with severity; the app decides which ones "
            "to show. Do not report typos, punctuation, capitalisation or speech recognition errors. "
            "Empty list when the message has no mistakes and at the start of a session."
        )
    )
    reply: str = Field(
        description=(
            "What the tutor says next, in English, read aloud by text-to-speech: 2-4 short sentences in plain "
            "text (no markdown, emoji, lists or brackets), ending with one question. Weave in the correct form "
            "of each mistake that the correction style asks to fix, naturally and without lecturing, "
            "e.g. 'Oh, you went to Spain last summer? Nice!'."
        )
    )
    reply_pl: str = Field(
        description=(
            "The reply translated into natural Polish, same meaning and tone, plain text, shown on screen only. "
            "The learner's gender is unknown, even when their name seems to suggest it: never use gendered "
            "past-tense forms for the learner (write 'Udało ci się pojechać?' or 'Co tam było?', not 'Pojechałeś?' "
            "or 'Co robiłaś?'). Empty string if you cannot translate it well."
        )
    )


MAX_SUMMARY_ITEMS = 3


class SummaryCorrection(BaseModel):
    """One of the most important mistakes from the whole session."""

    you_said: str = Field(description="The learner's words with the mistake, copied exactly from one of their messages.")
    better: str = Field(description="The same words the way a native speaker would say them at the learner's level.")
    explanation_pl: str = Field(description="One short sentence in Polish (at most 15 words) naming the rule.")


class Vocabulary(BaseModel):
    """A word or phrase worth learning, connected to what the learner talked about."""

    word: str = Field(description="English word or short phrase that would have helped the learner in this conversation.")
    meaning_pl: str = Field(description="Its meaning in Polish, a few words.")
    example: str = Field(description="One short English sentence using it, about the session topic.")


class Summary(BaseModel):
    """Feedback for the learner after the session. Fill the fields in order."""

    top_corrections: Annotated[list[SummaryCorrection], MaxLen(MAX_SUMMARY_ITEMS)] = Field(
        description=(
            f"At most {MAX_SUMMARY_ITEMS} mistakes that matter most: repeated ones and ones that change the meaning "
            "first. Only mistakes the learner really made; empty list when there were none."
        )
    )
    useful_vocabulary: Annotated[list[Vocabulary], MaxLen(MAX_SUMMARY_ITEMS)] = Field(
        description=f"At most {MAX_SUMMARY_ITEMS} words or phrases at or slightly above the learner's level."
    )
    strengths: Annotated[list[str], MaxLen(MAX_SUMMARY_ITEMS)] = Field(
        description=(
            f"At most {MAX_SUMMARY_ITEMS} specific things the learner did well, each one short sentence in Polish, "
            "e.g. 'Dobrze używasz czasu przeszłego w pytaniach.'"
        )
    )
    tip_pl: str = Field(description="One concrete tip in Polish for the next session, one or two sentences.")
