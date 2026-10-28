import pytest
from openai.lib._pydantic import to_strict_json_schema
from pydantic import ValidationError

from tutor import llm
from tutor.profiles import Profile
from tutor.schemas import MAX_CORRECTIONS, Correction, TutorTurn
from tutor.session import Session


def correction(you_said, severity="important"):
    return Correction(
        you_said=you_said, better="fixed", mistake_type="grammar", severity=severity, explanation_pl="Bo tak."
    )


@pytest.mark.parametrize("model", [TutorTurn, Correction])
def test_every_field_is_described(model):
    assert model.__doc__
    for name, field in model.model_fields.items():
        assert field.description and len(field.description) > 40, name


def test_field_order_is_analysis_corrections_reply():
    assert list(TutorTurn.model_fields) == ["analysis", "corrections", "reply"]


def test_strict_schema_carries_rules():
    schema = to_strict_json_schema(TutorTurn)
    correction_schema = schema["$defs"]["Correction"]["properties"]

    assert schema["properties"]["corrections"]["maxItems"] == MAX_CORRECTIONS
    assert correction_schema["severity"]["enum"] == ["important", "minor"]
    assert correction_schema["mistake_type"]["enum"] == ["grammar", "word_choice", "polish_word", "word_order"]
    assert schema["description"] == TutorTurn.__doc__


def test_too_many_corrections_are_rejected():
    with pytest.raises(ValidationError):
        TutorTurn(analysis="x", corrections=[correction("a")] * (MAX_CORRECTIONS + 1), reply="Hi?")


@pytest.mark.parametrize(
    ("style", "expected"),
    [("gentle", ["I go there"]), ("strict", ["I go there", "the beach"])],
)
def test_visible_corrections_follow_style(style, expected):
    turn = TutorTurn(
        analysis="x",
        corrections=[correction("I go there"), correction("the beach", "minor"), correction("not said")],
        reply="Nice?",
    )
    visible = llm.visible_corrections(turn, "Yesterday I go there to the beach", style)
    assert [c.you_said for c in visible] == expected


def test_start_drops_corrections(monkeypatch):
    monkeypatch.setattr(
        llm, "_ask", lambda instructions, messages: TutorTurn(analysis="x", corrections=[correction("x")], reply="Hi?")
    )
    session = Session(profile=Profile(id="a", name="A"), topic="Food")
    assert llm.start(session).corrections == []


def test_ask_retries_once_after_invalid_output(monkeypatch):
    turn = TutorTurn(analysis="x", corrections=[], reply="Hi?")
    try:
        TutorTurn.model_validate({})
    except ValidationError as error:
        invalid = error

    results = [invalid, type("Parsed", (), {"output_parsed": turn})()]

    class Responses:
        def parse(self, **kwargs):
            result = results.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

    monkeypatch.setattr(llm, "get_client", lambda: type("Client", (), {"responses": Responses()})())
    assert llm._ask("instructions", []) == turn
    assert results == []
