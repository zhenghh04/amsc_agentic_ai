"""Small helpers for keeping MCP tool responses context-bounded."""

from __future__ import annotations

import json
import re
from typing import Any


DEFAULT_TEXT_LIMIT = 12_000
DEFAULT_FILE_LIMIT = 20_000
DEFAULT_LOG_LIMIT = 12_000
MAX_TAIL_LINES = 200


# Patterns for secrets that show up in ClearML worker logs / agent config dumps.
# Order matters: collapse the multi-line config block first, then redact any
# stray key=value pairs that survive (e.g. when the dump is split across
# multiple log events).
_REDACT_PLACEHOLDER = "<redacted>"
_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Collapse the entire `Current configuration (clearml_agent ...)` block
    # that the ClearML worker dumps at task start. It is multi-line, ~200
    # lines, and contains api.credentials.access_key in plaintext. The block
    # ends at a blank line followed by either "Executing task id" or
    # "Running task id" (ClearML worker convention) or end-of-input.
    (
        re.compile(
            r"Current configuration \(clearml_agent[^\n]*\n"
            r".*?"
            r"(?=\n\n(?:Executing task id|Running task id|Summary - installed)"
            r"|\n\n[A-Z][a-z]"
            r"|\Z)",
            re.DOTALL,
        ),
        "[ClearML agent config dump scrubbed by MCP]",
    ),
    # key/value lines that name common credential fields. Matches both
    # bare `access_key = X` and dotted `api.credentials.access_key = X`.
    (
        re.compile(
            r"(?im)^(?P<prefix>[ \t]*[\w.\-]*?(?:access[_-]?key|secret[_-]?key|"
            r"api[_-]?key|api[_-]?token|auth[_-]?token|bearer[_-]?token|"
            r"password|passwd|git_pass|client[_-]?secret)[ \t]*[:=][ \t]*)"
            r"(?P<value>[^\s].*)$"
        ),
        lambda m: f"{m.group('prefix')}{_REDACT_PLACEHOLDER}",
    ),
    # JSON-style "access_key": "value"
    (
        re.compile(
            r'(?i)("(?:access[_-]?key|secret[_-]?key|api[_-]?key|api[_-]?token|'
            r'auth[_-]?token|bearer[_-]?token|password|passwd|git_pass|'
            r'client[_-]?secret)"[ \t]*:[ \t]*")[^"\n]+(")'
        ),
        lambda m: f"{m.group(1)}{_REDACT_PLACEHOLDER}{m.group(2)}",
    ),
    # Authorization: Bearer <token>
    (
        re.compile(r"(?i)(authorization[ \t]*:[ \t]*bearer[ \t]+)\S+"),
        lambda m: f"{m.group(1)}{_REDACT_PLACEHOLDER}",
    ),
    # URLs with embedded user:pass — https://user:pass@host
    (
        re.compile(r"(https?://)([^:/\s@]+):([^@/\s]+)@"),
        lambda m: f"{m.group(1)}{_REDACT_PLACEHOLDER}:{_REDACT_PLACEHOLDER}@",
    ),
    # Env-var dumps of tokens/keys/passwords. Catches both
    # `GLOBUS_TRANSFER_TOKEN=AbCdEf...` (env dump) and
    # `export OPENAI_API_KEY=sk-...` (script line). Requires a long enough
    # value run (20+ chars) to avoid redacting placeholder strings.
    (
        re.compile(
            r"(?im)^(?P<prefix>(?:export[ \t]+)?[A-Z][A-Z0-9_]*"
            r"(?:TOKEN|KEY|SECRET|PASSWORD|PASSWD|CREDENTIAL)"
            r"[A-Z0-9_]*[ \t]*=[ \t]*)"
            r"[A-Za-z0-9_\-\./+=]{20,}"
        ),
        lambda m: f"{m.group('prefix')}{_REDACT_PLACEHOLDER}",
    ),
    # Same shape but inside a non-line-anchored context (e.g. inline in a
    # log message: `... GLOBUS_TRANSFER_TOKEN=AgaB...`). Looser \b boundary.
    (
        re.compile(
            r"\b(?P<prefix>[A-Z][A-Z0-9_]*"
            r"(?:TOKEN|KEY|SECRET|PASSWORD|PASSWD|CREDENTIAL)"
            r"[A-Z0-9_]*[ \t]*=[ \t]*)"
            r"[A-Za-z0-9_\-\./+=]{20,}"
        ),
        lambda m: f"{m.group('prefix')}{_REDACT_PLACEHOLDER}",
    ),
]


def scrub_secrets(text: str) -> str:
    """Best-effort redact credentials from text destined for the LLM context.

    Defense in depth — ClearML already redacts many fields with `****`, but
    its worker config dump leaks `api.credentials.access_key` in plaintext
    at task start, and ad-hoc env dumps from user scripts may surface tokens.
    This pass collapses known noisy blocks and replaces obvious key=value
    pairs with `<redacted>`. It is not a substitute for not-logging-secrets,
    but it stops the most common leaks reaching the model.
    """
    if not isinstance(text, str) or not text:
        return text
    out = text
    for pattern, replacement in _SECRET_PATTERNS:
        out = pattern.sub(replacement, out)
    return out


def clamp_int(value: int, *, minimum: int, maximum: int) -> int:
    """Clamp integer values used for line/log limits."""
    try:
        value = int(value)
    except Exception:
        value = minimum
    return max(minimum, min(value, maximum))


def _split_lines_keepends(text: str) -> list[str]:
    lines = text.splitlines()
    if text.endswith("\n"):
        lines.append("")
    return lines


def select_text_window(text: str, mode: str = "head", lines: int = 50) -> str:
    """Return a head/tail/window selection from text."""
    mode = (mode or "head").lower()
    if mode == "view":
        return text
    n = clamp_int(lines, minimum=1, maximum=MAX_TAIL_LINES)
    items = _split_lines_keepends(text)
    if mode == "tail":
        return "\n".join(items[-n:])
    return "\n".join(items[:n])


def bound_text(
    text: Any,
    *,
    max_chars: int = DEFAULT_TEXT_LIMIT,
    mode: str = "head",
    label: str = "content",
    full: bool = False,
    scrub: bool = True,
) -> str:
    """Return text with an explicit truncation marker when context-bounded.

    If `full=True` or `max_chars <= 0`, no truncation is applied.
    Tail mode keeps the end of the selected text; other modes keep the front.
    `scrub=True` (default) runs `scrub_secrets` before truncation so the
    redaction is consistent regardless of which window survives.
    """
    if not isinstance(text, str):
        text = str(text)
    if scrub:
        text = scrub_secrets(text)
    if full or max_chars <= 0 or len(text) <= max_chars:
        return text

    max_chars = max(200, int(max_chars))
    mode = (mode or "head").lower()
    marker = (
        f"[context-bounded {label}: original_chars={len(text)}, "
        f"returned_chars={max_chars}, truncated=true. "
        "Pass full=true or max_chars=0 to request full content.]\n"
    )
    keep = max(1, max_chars - len(marker))
    if mode == "tail":
        return marker + text[-keep:]
    return marker + text[:keep]


def bounded_file_text(
    text: Any,
    *,
    path: str,
    mode: str = "head",
    lines: int = 50,
    max_chars: int = DEFAULT_FILE_LIMIT,
    full: bool = False,
) -> str:
    """Apply head/tail selection and a character bound for file content."""
    selected = str(text)
    if not full:
        selected = select_text_window(selected, mode=mode, lines=lines)
    return bound_text(
        selected,
        max_chars=max_chars,
        mode=mode,
        label=f"file path={path!r} mode={mode!r}",
        full=full,
    )


def compact_clearml_log(data: Any, *, max_chars: int = DEFAULT_LOG_LIMIT, full: bool = False) -> str:
    """Format ClearML task logs as compact text instead of large nested JSON."""
    entries = _extract_log_entries(data)
    lines = [_format_log_entry(entry) for entry in entries]
    text = "\n".join(line for line in lines if line)
    if not text:
        text = json.dumps(data, indent=2, default=str)
    return bound_text(text, max_chars=max_chars, mode="tail", label="clearml_log", full=full)


def bound_nested_strings(
    data: Any,
    *,
    max_chars: int = DEFAULT_LOG_LIMIT,
    full: bool = False,
    mode: str = "tail",
) -> Any:
    """Recursively bound large strings inside JSON-like data structures."""
    if full or max_chars <= 0:
        return data
    if isinstance(data, str):
        return bound_text(data, max_chars=max_chars, mode=mode, label="nested_string")
    if isinstance(data, list):
        return [bound_nested_strings(item, max_chars=max_chars, full=full, mode=mode) for item in data]
    if isinstance(data, tuple):
        return [bound_nested_strings(item, max_chars=max_chars, full=full, mode=mode) for item in data]
    if isinstance(data, dict):
        return {
            key: bound_nested_strings(value, max_chars=max_chars, full=full, mode=mode)
            for key, value in data.items()
        }
    return data


def _extract_log_entries(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("events", "log", "logs", "entries", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        if len(data) == 1:
            value = next(iter(data.values()))
            if isinstance(value, list):
                return value
    return [data]


def _format_log_entry(entry: Any) -> str:
    if isinstance(entry, str):
        return entry
    if not isinstance(entry, dict):
        return str(entry)

    timestamp = entry.get("timestamp") or entry.get("time") or entry.get("created")
    level = entry.get("level") or entry.get("type") or entry.get("severity")
    worker = entry.get("worker") or entry.get("worker_id")
    message = (
        entry.get("msg")
        or entry.get("message")
        or entry.get("text")
        or entry.get("console")
        or entry.get("log")
    )
    if message is None:
        message = json.dumps(entry, default=str, sort_keys=True)

    prefix = " ".join(str(v) for v in (timestamp, level, worker) if v not in (None, ""))
    return f"{prefix} {message}".strip()
