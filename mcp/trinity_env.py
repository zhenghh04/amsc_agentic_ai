"""Centralized per-user .env resolution for all Trinity MCP servers.

WHY THIS EXISTS
---------------
Claude Code spawns project-local (repo-relative) MCP stdio servers with their
``CLAUDE_*`` environment variables STRIPPED. So the per-user ``CLAUDE_ENV_FILE``
that Trinity sets on the agent process never reaches the MCP servers — every
server would fall back to the shared repo-root ``.env`` and read/write one
tenant's tokens into the file all tenants load (a cross-tenant credential leak).

Non-``CLAUDE_`` variables DO survive that hop, so Trinity exports
``TRINITY_ENV_DIR`` (the directory that holds this session's private ``.env``),
and every server resolves ``$TRINITY_ENV_DIR/.env`` through this one module.

Resolution order (first hit wins):
  1. ``$TRINITY_ENV_DIR/.env``   — per-user, set by Trinity (the normal path)
  2. ``$CLAUDE_ENV_FILE``        — non-stripped contexts (e.g. ``--mcp-config``)
  3. ``<repo-root>/.env``        — standalone CLI use outside Trinity
"""
from __future__ import annotations

import os
from pathlib import Path

# Repo root = parent of mcp/ (this file lives at mcp/trinity_env.py).
_REPO_ROOT = Path(__file__).resolve().parent.parent


def env_file() -> Path:
    """Absolute path to this session's credentials .env (see module docstring)."""
    d = os.environ.get("TRINITY_ENV_DIR", "").strip()
    if d:
        return Path(d) / ".env"
    f = os.environ.get("CLAUDE_ENV_FILE", "").strip()
    if f:
        return Path(f)
    return _REPO_ROOT / ".env"


def read_value(key: str) -> str:
    """Current value of ``key`` read STRAIGHT from env_file(), bypassing
    os.environ.

    MCP servers are long-lived and their ``_load_env`` deliberately does not
    overwrite an already-set os.environ var — so a token rotated externally
    (login/refresh) never reaches a call that reads os.environ. Credential reads
    must go through here so they always see the freshest value on disk.
    """
    f = env_file()
    if not f.exists():
        return ""
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        k, _, v = line.partition("=")
        if k.strip() == key:
            v = v.strip()
            # tolerate single/double quoted values (see user_tokens._env_quote)
            if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
                v = v[1:-1]
            return v
    return ""
