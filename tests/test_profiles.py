import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import HTTPException
from pydantic import ValidationError

import app
from tutor import profiles
from tutor.profiles import DEFAULT_INTERESTS, Profile


def expect(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type as error:
        return error
    raise AssertionError(f"{fn.__name__}{args}{kwargs} did not raise {exc_type.__name__}")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        profiles.PROFILES_DIR = Path(tmp) / "profiles"

        assert app.get_profiles() == []

        new = Profile(id="michal", name="Michał")
        assert new.level == "B1"
        assert new.interests == DEFAULT_INTERESTS
        assert new.correction_style == "gentle"

        saved = app.put_profile("michal", new)
        assert app.get_profile("michal") == saved
        assert "Michał" in (profiles.PROFILES_DIR / "michal.json").read_text(encoding="utf-8")
        assert [p.id for p in app.get_profiles()] == ["michal"]

        assert expect(HTTPException, app.get_profile, "nobody").status_code == 404
        for bad_id in ["..", "../.env", "Michal", "a" * 33, ""]:
            assert expect(HTTPException, app.get_profile, bad_id).status_code == 400
            expect(ValueError, profiles.load_profile, bad_id)
        assert expect(HTTPException, app.put_profile, "other", new).status_code == 400

        expect(ValidationError, Profile, id="../x", name="X")
        expect(ValidationError, Profile, id="x", name="X", level="D1")
        expect(ValidationError, Profile, id="x", name="X", goals="a" * 301)
        expect(ValidationError, Profile, id="x", name="X", interests=["t"] * 21)

        (profiles.PROFILES_DIR / "broken.json").write_text("{not json", encoding="utf-8")
        assert [p.id for p in app.get_profiles()] == ["michal"]

    print("OK: profiles")


if __name__ == "__main__":
    main()
