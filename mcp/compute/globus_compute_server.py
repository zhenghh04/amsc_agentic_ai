# Author: Huihuo Zheng, huihuo.zheng@anl.gov
# Copyright: Trinity Science 2026

"""MCP server for Globus Compute — run Python functions and shell commands on a
facility Multi-User Endpoint (MEP), from your laptop, via FastMCP.

WHAT THIS IS
------------
Globus Compute (formerly funcX) is function-as-a-service for HPC: the facility
runs a Multi-User Endpoint (MEP) that launches *your* functions inside *your*
scheduler allocation. You never create or babysit an endpoint — you register a
function, then run it on the MEP by UUID. This complements the IRI servers
(``alcf-iri`` etc.): IRI submits a whole batch job; Globus Compute runs a Python
function (or a shell command) on a compute node and hands back the return value.

The taught path is **ALCF / Polaris** (the facility MEP that Session 02 of the
Service-Enabled-Science workshop validated). The tools are endpoint-driven, so
the *same* tools reach any facility MEP once you have a token for it — see the
"Extending to other facilities" note in part3_iri/09_remote_functions.md.

TWO LOAD-BEARING LESSONS (ported from SES Session 02)
-----------------------------------------------------
1. **Register from source, not a pickle.** The MEP workers may run a different
   Python version than your laptop; pickling a function across versions throws a
   ``ManagerLost`` serialization error. ``register_function`` here ships the
   function *source* (``Client.register_source_code``) so the worker recompiles
   it locally — version-safe, the same outcome the workshop got with the
   ``AllCodeStrategies`` serializer.
2. **Mind the filesystem the MEP can see.** Functions run *on the compute node*,
   so any path they touch must live on a node-visible filesystem — on Polaris
   that is ``home``, ``eagle``, or ``grand``. **Polaris cannot see Aurora's
   ``/flare``.** For the known MEPs this server injects
   ``#PBS -l filesystems=home:eagle:grand`` into the endpoint config unless you
   set your own ``scheduler_options``.

AUTH
----
Uses ``GLOBUS_COMPUTE_TOKEN`` from ``.env`` (minted alongside the transfer token
by ``scripts/auth/globus_auth.py``). The token is re-read from the file on every
call, so a refresh mid-session is picked up with no restart.
"""

import ast
import asyncio
import json
import logging
import os
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # mcp/ root

from mcp.server.fastmcp import FastMCP

from context_utils import bound_nested_strings, clamp_int
from trinity_env import env_file as _trinity_env_file, read_value as _read_env_value

logger = logging.getLogger(__name__)

_ENV_FILE = _trinity_env_file()


def _load_env() -> None:
    """Load .env into os.environ without overwriting existing non-empty vars."""
    if not _ENV_FILE.exists():
        return
    for line in _ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        existing = os.environ.get(key, "")
        if key and (not existing or existing.startswith("${")):
            os.environ[key] = value


def _update_env(key: str, value: str) -> None:
    """Update or add a key=value pair in the .env file (as the IRI servers do).

    Needed because credential reads go through ``trinity_env.read_value``, which
    reads the file and bypasses ``os.environ`` on purpose: a token handed to
    ``authenticate()`` has to land on disk or no later call would ever see it.
    """
    lines: list[str] = []
    found = False
    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text().splitlines():
            if line.lstrip().startswith(f"export {key}=") or line.startswith(f"{key}="):
                lines.append(f"{key}={value}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"{key}={value}")
    _ENV_FILE.write_text("\n".join(lines) + "\n")


_load_env()

mcp = FastMCP("globus-compute")

# ── Facility MEPs ────────────────────────────────────────────────────────
# Named shortcuts for the facility Multi-User Endpoints. Pass "polaris"/"crux"
# or a raw UUID anywhere an endpoint_id is expected. (UUIDs from SES Session 02.)
_MEP_UUIDS: dict[str, str] = {
    "polaris": "9a947ba5-f537-4681-acf3-cc66485aadec",
    "crux": "fd8b54bb-9452-411d-8e3a-09408156a886",
}
_MEP_SET = set(_MEP_UUIDS.values())

# The Globus-Compute token var. Facility-specific MEPs (NERSC/OLCF) use their own
# tokens; add them here + a matching scripts/auth helper to extend reach.
_TOKEN_VAR = "GLOBUS_COMPUTE_TOKEN"

# In-process name -> function UUID registry (not persisted). Lets you register a
# function once and run it by a friendly name within a session.
_registered: dict[str, str] = {}
# Cache the source wrapper used by run_shell_command so we register it once.
_shell_func_id: str | None = None

# Single cached client plus the exact token it was built from. Compared in full,
# not by prefix: two different tokens can share a prefix, and a stale authorizer
# would then survive a rotation — the opposite of this server's re-read-the-token
# behaviour.
_client: object | None = None
_client_token: str | None = None


def _fmt(data) -> str:
    """Format a response as indented JSON (matches the IRI servers' _fmt)."""
    return json.dumps(data, indent=2, default=str)


def _resolve_endpoint(endpoint_id: str) -> str:
    """Map a 'polaris'/'crux' shortcut to its MEP UUID; pass UUIDs through."""
    key = (endpoint_id or "").strip()
    return _MEP_UUIDS.get(key.lower(), key)


def _globus_compute_deps():
    """Import globus_compute_sdk / globus_sdk lazily (heavy deps, isolated env)."""
    from globus_compute_sdk import Client
    from globus_sdk import AccessTokenAuthorizer
    return Client, AccessTokenAuthorizer


def _get_client():
    """Build (or reuse) a Globus Compute Client from the on-disk token.

    Never constructs a bare ``Client()`` with no authorizer — that triggers an
    interactive browser/CLI login that blocks on stdin and corrupts the MCP
    stdio channel. Raises a RuntimeError with a fix instead.
    """
    token = _read_env_value(_TOKEN_VAR)
    if not token:
        raise RuntimeError(
            f"No {_TOKEN_VAR} in {_ENV_FILE}. Mint one with: "
            "python scripts/auth/globus_auth.py ensure_valid"
        )
    global _client, _client_token, _shell_func_id
    if _client is None or token != _client_token:
        # A token change can also be an *identity* change, and function UUIDs are
        # owned by the principal that registered them. Drop the name->UUID caches
        # with the client, or a later run_function would hand this identity a
        # registration it may not be allowed to invoke. Done here rather than in
        # authenticate() because the token is re-read every call, so this also
        # catches a rotation performed outside this process.
        if _client_token is not None and token != _client_token:
            _registered.clear()
            _shell_func_id = None
        Client, AccessTokenAuthorizer = _globus_compute_deps()
        _client = Client(authorizer=AccessTokenAuthorizer(token))
        _client_token = token
    return _client


def _handle_error(exc: Exception) -> str:
    """Turn an SDK exception into an actionable, agent-facing message."""
    text = str(exc)
    low = text.lower()
    if "401" in text or "unauthorized" in low or "authorizationrequired" in low:
        return (
            f"Authentication error: {text}\n"
            "The Globus Compute token is missing or expired. Refresh it with: "
            "python scripts/auth/globus_auth.py ensure_valid  (then retry)."
        )
    if "taskpending" in low or "task is pending" in low or "not yet available" in low:
        return f"Task is still running — poll get_result/get_task_status again shortly. ({text})"
    return f"Error: {text}"


def _first_def_name(source: str) -> str:
    """Return the name of the first *top-level* `def`/`async def` in source.

    Parses the AST and looks only at module-level nodes: a regex over lines
    would happily return a nested helper or a class method, neither of which is
    registrable as the function the caller meant.
    """
    try:
        tree = ast.parse(textwrap.dedent(source))
    except SyntaxError:
        return ""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name
    return ""


def _merge_mep_defaults(endpoint: str, cfg: dict) -> dict:
    """Inject the Polaris-visible filesystems line for known MEPs.

    Functions run on the compute node, so paths must be on a node-visible
    filesystem (home/eagle/grand). Polaris cannot see Aurora's /flare. We only
    set this when the caller hasn't supplied their own scheduler_options.
    """
    if endpoint not in _MEP_SET:
        return cfg
    cfg = dict(cfg)
    so = str(cfg.get("scheduler_options", ""))
    if "filesystems" not in so:
        line = "#PBS -l filesystems=home:eagle:grand"
        cfg["scheduler_options"] = f"{so}\n{line}".strip() if so else line
    return cfg


def _mep_config_ready(endpoint: str, cfg: dict) -> str:
    """Return an error string if a MEP run is missing required config, else ''.

    A facility MEP launches your function inside a scheduler allocation, so it
    needs at least an ``account`` (and usually a ``queue``). Catch the common
    "forgot the account" mistake before the submit instead of after.
    """
    if endpoint in _MEP_SET and not cfg.get("account"):
        return (
            "Running on a facility MEP needs an account. Pass "
            'user_endpoint_config_json=\'{"account": "<your-account>", '
            '"queue": "debug"}\' (same account you would charge an IRI job to).'
        )
    return ""


# ── Authentication ───────────────────────────────────────────────────────


@mcp.tool()
async def authenticate(token: str = "") -> str:
    """Store/verify a Globus Compute token for remote function execution.

    Args:
        token: A Globus access token with the Compute scope. If empty, falls
               back to GLOBUS_COMPUTE_TOKEN in .env (re-read at call time), so a
               bare authenticate() succeeds whenever .env already has a fresh
               token. Mint one with `python scripts/auth/globus_auth.py ensure_valid`.
               A token passed here is saved to that same file (as the IRI
               servers do), so later calls and restarts pick it up.

    Verifies the token with a real authenticated call to the Compute service
    (listing your own endpoints), so an expired or wrong token is reported here
    instead of surfacing as a confusing failure in a later tool. Other tools also
    read the token fresh from .env, so a refreshed token needs no restart.
    """
    token = token.strip()
    explicit = bool(token)
    token = token or _read_env_value(_TOKEN_VAR)
    if not token:
        return (
            f"Error: no token provided and {_TOKEN_VAR} not found in {_ENV_FILE}. "
            "Run `python scripts/auth/globus_auth.py ensure_valid` to mint one, then retry."
        )
    if explicit:
        # _get_client resolves the token through trinity_env.read_value, which
        # reads the file and deliberately bypasses os.environ. Persist it the way
        # the IRI servers do, or a token handed to this call would be ignored in
        # favour of whatever is already on disk.
        _update_env(_TOKEN_VAR, token)
    os.environ[_TOKEN_VAR] = token
    try:
        client = _get_client()
        # Constructing the client does no network I/O, so it cannot tell a good
        # token from a bad one. Make an account-scoped call instead: listing your
        # own endpoints depends only on the token, unlike probing a specific MEP,
        # which would also fail when that endpoint is merely down or draining.
        await asyncio.to_thread(client.get_endpoints)
        if explicit:
            return f"Globus Compute authenticated. Token saved to {_ENV_FILE}."
        return f"Globus Compute authenticated (token from {_ENV_FILE})."
    except Exception as exc:
        return _handle_error(exc)


# ── Endpoint status ──────────────────────────────────────────────────────


@mcp.tool()
async def get_endpoint_status(endpoint_id: str) -> str:
    """Report whether a Globus Compute endpoint is online and its queue depth.

    Args:
        endpoint_id: "polaris", "crux", or an endpoint UUID.

    Returns the endpoint status (online/offline) and details. Does not start any
    compute. Requires a valid token.
    """
    ep = _resolve_endpoint(endpoint_id)
    try:
        client = _get_client()
        status = await asyncio.to_thread(client.get_endpoint_status, ep)
        return _fmt({"endpoint": ep, "status": status})
    except Exception as exc:
        return _handle_error(exc)


# ── Registration ─────────────────────────────────────────────────────────


@mcp.tool()
async def register_function(
    function_code: str,
    function_name: str = "",
    description: str = "",
) -> str:
    """Register a Python function on Globus Compute so it can be run on a MEP.

    Registers the function's SOURCE (not a pickle) so a MEP worker on a different
    Python version recompiles it locally — this is what avoids the ManagerLost
    serialization error (the SES `AllCodeStrategies` lesson).

    Args:
        function_code: The function definition as source, e.g.
            "def hello():\n    import socket\n    return socket.gethostname()".
            Put every import INSIDE the function body — the worker has only what
            the source carries.
        function_name: Which def in the source to register. Defaults to the first
            top-level def found.
        description: Optional human-readable description.

    Returns the function UUID (also stored under `function_name` for this session,
    so run_function accepts either the UUID or the name). Requires a valid token.
    """
    code = textwrap.dedent(function_code).strip()
    if not code:
        return "Error: function_code is empty."
    name = function_name.strip() or _first_def_name(code)
    if not name:
        return "Error: could not find a `def` in function_code; pass function_name explicitly."
    try:
        client = _get_client()
        if hasattr(client, "register_source_code"):
            func_id = await asyncio.to_thread(
                client.register_source_code,
                source=code,
                function_name=name,
                description=description or name,
            )
        else:
            # Fallback for older SDKs without register_source_code: exec + object
            # registration (uses the default serializer — version-sensitive).
            namespace: dict = {}
            exec(code, namespace)  # noqa: S102 — tutorial tool, source is user-authored
            func = namespace.get(name)
            if not callable(func):
                return f"Error: '{name}' is not a callable defined in function_code."
            func_id = await asyncio.to_thread(
                client.register_function, func, description=description or name
            )
        _registered[name] = str(func_id)
        return _fmt({"function_name": name, "function_id": str(func_id)})
    except Exception as exc:
        return _handle_error(exc)


@mcp.tool()
async def list_registered_functions() -> str:
    """List functions registered in this session (name -> UUID).

    This is an in-process registry; it resets when the server restarts. Functions
    stay registered on the Globus Compute service and can still be run by UUID.
    """
    if not _registered:
        return "No functions registered in this session. Use register_function first."
    return _fmt(_registered)


# ── Execution ────────────────────────────────────────────────────────────


@mcp.tool()
async def run_function(
    function_id: str,
    endpoint_id: str,
    args_json: str = "[]",
    kwargs_json: str = "{}",
    user_endpoint_config_json: str = "{}",
) -> str:
    """Run a registered function on an endpoint and return a task_id (async).

    Args:
        function_id: The UUID from register_function, or a name registered this
            session (see list_registered_functions).
        endpoint_id: "polaris", "crux", or an endpoint UUID.
        args_json: JSON list of positional args, e.g. "[5, 10]".
        kwargs_json: JSON object of keyword args, e.g. '{"n": 3}'.
        user_endpoint_config_json: JSON object passed to the MEP at submit time.
            For a facility MEP you MUST include "account"; typically also
            "queue" (e.g. "debug"), optionally "walltime", "nodes_per_block".
            The filesystems line (home:eagle:grand) is added automatically for
            the known MEPs. Example:
            '{"account": "MyProject", "queue": "debug", "walltime": "00:10:00"}'.

    This returns as soon as the task is accepted — it does NOT wait for the
    result. Poll get_task_status / get_result with the returned task_id.
    Requires a valid token.
    """
    ep = _resolve_endpoint(endpoint_id)
    try:
        args = json.loads(args_json or "[]")
        if not isinstance(args, list):
            return "Error: args_json must be a JSON list, e.g. \"[5, 10]\"."
        kwargs = json.loads(kwargs_json or "{}")
        if not isinstance(kwargs, dict):
            return "Error: kwargs_json must be a JSON object, e.g. '{\"n\": 3}'."
        cfg = json.loads(user_endpoint_config_json or "{}")
        if not isinstance(cfg, dict):
            return "Error: user_endpoint_config_json must be a JSON object."
    except json.JSONDecodeError as exc:
        return f"Error parsing JSON argument: {exc}"

    func_uuid = _registered.get(function_id, function_id)
    msg = _mep_config_ready(ep, cfg)
    if msg:
        return msg
    cfg = _merge_mep_defaults(ep, cfg)

    try:
        client = _get_client()
        task_id = await asyncio.to_thread(
            _submit, client, ep, func_uuid, tuple(args), kwargs, cfg
        )
        if not task_id:
            return "Error: submission returned no task_id."
        return _fmt({
            "task_id": task_id,
            "endpoint": ep,
            "function_id": func_uuid,
            "note": "Accepted. Poll get_result(task_id) until it returns a value.",
        })
    except Exception as exc:
        return _handle_error(exc)


def _submit(client, endpoint, func_uuid, args, kwargs, cfg):
    """Submit one invocation; returns a task_id. Runs in a worker thread.

    MEP runs need a user_endpoint_config, which only the batch API carries — so
    we use create_batch/batch_run whenever a config is present, and the simple
    client.run otherwise.
    """
    if cfg:
        batch = client.create_batch(user_endpoint_config=cfg)
        batch.add(func_uuid, args=args, kwargs=kwargs)
        result = client.batch_run(endpoint, batch)
        tasks = result.get("tasks", {}) if isinstance(result, dict) else {}
        ids = [tid for group in tasks.values() for tid in group]
        return ids[0] if ids else None
    return client.run(*args, endpoint_id=endpoint, function_id=func_uuid, **kwargs)


@mcp.tool()
async def get_task_status(task_id: str) -> str:
    """Get the status of a Globus Compute task (does not block for the result).

    Args:
        task_id: The task_id returned by run_function / run_shell_command.

    Returns pending/running/success/failed plus details. Requires a valid token.
    """
    try:
        client = _get_client()
        info = await asyncio.to_thread(client.get_task, task_id)
        return _fmt(info)
    except Exception as exc:
        return _handle_error(exc)


@mcp.tool()
async def get_result(task_id: str, max_chars: int = 12000, full: bool = False) -> str:
    """Fetch the return value of a completed Globus Compute task.

    Args:
        task_id: The task_id returned by run_function / run_shell_command.
        max_chars: Cap on returned string length (default 12000). 0 = no cap.
        full: If true, return the full result regardless of max_chars.

    If the task is still running this returns a "still running" message — poll
    again. If the remote function raised, the exception is surfaced here.
    Requires a valid token.
    """
    try:
        client = _get_client()
        result = await asyncio.to_thread(client.get_result, task_id)
    except Exception as exc:
        return _handle_error(exc)
    bounded = bound_nested_strings(
        result, max_chars=clamp_int(max_chars, minimum=0, maximum=200000),
        full=full, mode="tail",
    )
    return _fmt({"task_id": task_id, "result": bounded})


@mcp.tool()
async def run_shell_command(
    command: str,
    endpoint_id: str,
    user_endpoint_config_json: str = "{}",
    timeout: int = 120,
    max_chars: int = 12000,
    full: bool = False,
) -> str:
    """Run a shell command on a compute node via the MEP and return its output.

    Convenience wrapper for quick one-shot commands (e.g. "hostname; nvidia-smi
    -L"). It registers a tiny subprocess runner (from source, version-safe),
    submits your command, and polls for the result up to `timeout` seconds.

    Args:
        command: The shell command line to run, e.g. "hostname && nvidia-smi -L".
        endpoint_id: "polaris", "crux", or an endpoint UUID.
        user_endpoint_config_json: JSON object for the MEP (see run_function);
            for a facility MEP you MUST include "account".
        timeout: Seconds to wait for the result before returning the task_id so
            you can poll get_result yourself (default 120, max 1800).
        max_chars: Cap on returned output length (default 12000). 0 = no cap.
        full: If true, return the full output regardless of max_chars.

    Output is bounded the same way get_result bounds it, so a chatty command
    cannot flood the agent's context. If the command fails, the error is
    returned immediately rather than being reported as "still running".

    For anything longer-running than a quick probe, register a function and use
    run_function + get_result instead. Requires a valid token.
    """
    global _shell_func_id
    ep = _resolve_endpoint(endpoint_id)
    timeout = clamp_int(timeout, minimum=5, maximum=1800)
    try:
        cfg = json.loads(user_endpoint_config_json or "{}")
        if not isinstance(cfg, dict):
            return "Error: user_endpoint_config_json must be a JSON object."
    except json.JSONDecodeError as exc:
        return f"Error parsing user_endpoint_config_json: {exc}"

    msg = _mep_config_ready(ep, cfg)
    if msg:
        return msg
    cfg = _merge_mep_defaults(ep, cfg)

    shell_src = (
        "def _run_cmd(command):\n"
        "    import subprocess\n"
        "    p = subprocess.run(command, shell=True, capture_output=True, text=True)\n"
        "    return {'stdout': p.stdout, 'stderr': p.stderr, 'returncode': p.returncode}\n"
    )
    try:
        client = _get_client()
        if _shell_func_id is None:
            if hasattr(client, "register_source_code"):
                _shell_func_id = str(await asyncio.to_thread(
                    client.register_source_code,
                    source=shell_src, function_name="_run_cmd",
                    description="Run a shell command on the endpoint",
                ))
            else:
                ns: dict = {}
                exec(shell_src, ns)  # noqa: S102
                _shell_func_id = str(await asyncio.to_thread(
                    client.register_function, ns["_run_cmd"],
                    description="Run a shell command on the endpoint",
                ))
        task_id = await asyncio.to_thread(
            _submit, client, ep, _shell_func_id, (command,), {}, cfg
        )
        if not task_id:
            return "Error: submission returned no task_id."
    except Exception as exc:
        return _handle_error(exc)

    # Poll for the result up to `timeout`, then hand back the task_id.
    #
    # Poll get_task() rather than retrying get_result() blindly: only a *pending*
    # task should keep us in the loop. A remote exception, a bad task id, or an
    # expired token must surface immediately — swallowing those would report a
    # hard failure as "still running" once the timeout expired.
    waited = 0.0
    delay = 2.0
    while True:
        try:
            task = await asyncio.to_thread(client.get_task, task_id)
        except Exception as exc:
            return _handle_error(exc)
        if not (isinstance(task, dict) and task.get("pending")):
            break
        if waited >= timeout:
            return _fmt({
                "task_id": task_id,
                "command": command,
                "status": "still running",
                "note": f"Not finished within {timeout}s — poll get_result('{task_id}').",
            })
        sleep_for = min(delay, timeout - waited)
        await asyncio.sleep(sleep_for)
        waited += sleep_for
        delay = min(delay * 1.5, 15.0)

    # Terminal state: fetch the value once. If the remote function raised, the
    # SDK re-raises it here and _handle_error turns it into a readable message.
    try:
        result = await asyncio.to_thread(client.get_result, task_id)
    except Exception as exc:
        return _handle_error(exc)
    bounded = bound_nested_strings(
        result, max_chars=clamp_int(max_chars, minimum=0, maximum=200000),
        full=full, mode="tail",
    )
    return _fmt({"task_id": task_id, "command": command, "result": bounded})


# ── Entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
