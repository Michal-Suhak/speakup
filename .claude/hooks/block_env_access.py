"""PreToolUse hook: stop Claude from reading local env files or printing the API key.

Exit code 2 blocks the tool call and shows the reason to Claude.
"""

import json
import re
import sys

ENV_FILE = re.compile(r"(?<![\w-])\.env")
SHELL_LEAKS = [
    ENV_FILE,
    re.compile(r"OPENAI_API_KEY"),
    re.compile(r"\bprintenv\b"),
    re.compile(r"(^|[;&|(]\s*)(env|set|export)\s*($|[;&|)])"),
]


def blocked(tool: str, tool_input: dict) -> bool:
    if tool == "Bash":
        command = tool_input.get("command", "")
        return any(pattern.search(command) for pattern in SHELL_LEAKS)
    fields = (tool_input.get(key, "") for key in ("path", "glob", "pattern", "file_path"))
    return any(ENV_FILE.search(value) for value in fields if isinstance(value, str))


def main() -> None:
    event = json.load(sys.stdin)
    if blocked(event.get("tool_name", ""), event.get("tool_input") or {}):
        print(
            "Blocked: local env files and the API key are off limits (see .claude/rules/boundaries.md). "
            "Use env.example for variable names and `uv run python config.py` to check the key.",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
