"""PreToolUse hook: stop Claude from reading local env files or printing the API key.

Exit code 2 blocks the tool call and shows the reason to Claude. The checks are
deliberately broad: a blocked harmless command is cheap, a leaked key is not.
"""

import json
import re
import sys

ENV_FILE = re.compile(r"(?<![\w-])\.env")
NOT_SEP = r"[^|;&\n]*"
SHELL_LEAKS = [
    ENV_FILE,
    re.compile(r"OPENAI_API_KEY|os\.environ|getenv|dotenv_values"),
    re.compile(r"(?:^|(?<=\s))\.[^\s/'\"]*[*?\[]"),
    re.compile(rf"\b[ef]?grep\b{NOT_SEP}\s(-[a-zA-Z]*[rR]|--recursive|--directories)"),
    re.compile(rf"\brg\b{NOT_SEP}\s(--no-ignore|--hidden|-u)"),
    re.compile(rf"\bgit\s+grep\b{NOT_SEP}--(untracked|no-index|no-exclude-standard)"),
    re.compile(rf"\bfind\b{NOT_SEP}\s-(exec|execdir|ok)\b"),
    re.compile(r"\bxargs\b"),
    re.compile(r"\bprintenv\b|\bexport\s+-p\b|\bdeclare\s+-[a-zA-Z]*[xp]"),
    re.compile(r"(^|[;&|(]\s*)(env|set|export)(\s+-\S+)*\s*($|[;&|)])"),
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
            "Search code with `git grep` or `rg` (they skip ignored files), read env.example for variable "
            "names and run `uv run python config.py` to check the key.",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
