import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "block_env_access.py"
spec = importlib.util.spec_from_file_location("block_env_access", HOOK)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


@pytest.mark.parametrize(
    "command",
    [
        "cat .env",
        "cat ./.env.local",
        "head -n1 /Users/x/speakup/.env.backup",
        "grep KEY .env",
        "source .env",
        "cp .env /tmp/k",
        "cat .envrc",
        "echo $OPENAI_API_KEY",
        'uv run python -c "import config; print(config.OPENAI_API_KEY)"',
        "printenv",
        "env",
        "env -0",
        "ls && env | grep KEY",
        "set",
        "export -p",
        "declare -px",
        'uv run python -c "import config, os; print(dict(os.environ))"',
        'uv run python -c "from dotenv import dotenv_values; print(dotenv_values())"',
        'grep -rn "sk-" .',
        "grep -R KEY",
        "egrep --recursive KEY .",
        "cat .*",
        "head .e?v",
        "ls .[!.]*",
        "rg --no-ignore KEY",
        "rg -uu KEY",
        "rg --hidden KEY",
        "git grep --untracked KEY",
        "find . -type f -exec cat {} +",
        "ls -a | xargs cat",
    ],
)
def test_blocks_shell_access(command):
    assert hook.blocked("Bash", {"command": command})


@pytest.mark.parametrize(
    "command",
    [
        "cat env.example",
        "uv run python config.py",
        "uv sync",
        "ls .venv",
        "uv run pytest -q",
        "git status",
        "uv add python-dotenv",
        "uv run --env-file x.txt true",
        "git grep -n load_dotenv",
        "rg -n Profile tutor/",
        "grep -n KEY config.py",
        "ls tests/*.py",
        "cat ./README.md",
        "find . -name '*.py' -not -path './.venv/*'",
        "git log --oneline -3",
        "uv run uvicorn app:app --port 8799",
        "jq -r '.hooks.PreToolUse[0].hooks[0].command' settings.json",
        "ls '.*'",
    ],
)
def test_allows_normal_commands(command):
    assert not hook.blocked("Bash", {"command": command})


@pytest.mark.parametrize(
    ("tool", "tool_input"),
    [
        ("Read", {"file_path": "/repo/.env"}),
        ("Grep", {"pattern": "KEY", "path": ".env.local"}),
        ("Grep", {"pattern": "KEY", "glob": ".env*"}),
        ("Glob", {"pattern": "**/.env*"}),
    ],
)
def test_blocks_file_tools(tool, tool_input):
    assert hook.blocked(tool, tool_input)


def test_allows_file_tools_elsewhere():
    assert not hook.blocked("Read", {"file_path": "/repo/env.example"})
    assert not hook.blocked("Grep", {"pattern": "load_dotenv", "path": "config.py"})


def test_exit_codes():
    def run(event):
        return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event), text=True, capture_output=True)

    denied = run({"tool_name": "Bash", "tool_input": {"command": "cat .env"}})
    assert denied.returncode == 2
    assert "Blocked" in denied.stderr

    allowed = run({"tool_name": "Bash", "tool_input": {"command": "uv sync"}})
    assert allowed.returncode == 0
