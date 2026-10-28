import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import HTTPException
from pydantic import ValidationError

import app
from tutor import profiles
from tutor.profiles import DEFAULT_INTERESTS, BrokenProfile, InvalidProfileId, Profile


def expect(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type as error:
        return error
    raise AssertionError(f"{fn.__name__}{args}{kwargs} did not raise {exc_type.__name__}")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp) / "profiles"
        profiles.PROFILES_DIR = directory

        assert app.get_profiles() == []

        new = Profile(id="michal", name="Michał")
        assert new.level == "B1"
        assert new.interests == DEFAULT_INTERESTS
        assert new.correction_style == "gentle"

        saved = app.put_profile("michal", new)
        assert app.get_profile("michal") == saved
        assert "Michał" in (directory / "michal.json").read_text(encoding="utf-8")
        assert not list(directory.glob("*.tmp"))
        assert [p.id for p in app.get_profiles()] == ["michal"]

        assert expect(HTTPException, app.get_profile, "nobody").status_code == 404
        assert expect(HTTPException, app.put_profile, "other", new).status_code == 400
        for bad_id in ["..", "../.env", "Michal", "a" * 33, ""]:
            expect(InvalidProfileId, app.get_profile, bad_id)

        expect(ValidationError, Profile, id="../x", name="X")
        expect(ValidationError, Profile, id="x", name="X", level="D1")
        expect(ValidationError, Profile, id="x", name="X", goals="a" * 301)
        expect(ValidationError, Profile, id="x", name="X", interests=["t"] * 21)

        (directory / "broken.json").write_text("{not json", encoding="utf-8")
        (directory / "latin.json").write_bytes('{"id": "latin", "name": "Michał"}'.encode("cp1250"))
        (directory / "kasia.json").write_text(new.model_dump_json(), encoding="utf-8")
        assert [p.id for p in app.get_profiles()] == ["michal"]
        for broken_id in ["broken", "latin", "kasia"]:
            expect(BrokenProfile, app.get_profile, broken_id)

    print("OK: profiles")


if __name__ == "__main__":
    main()
