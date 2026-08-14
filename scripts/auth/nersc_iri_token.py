#!/usr/bin/env python3
"""Browser-based Globus authentication for the NERSC IRI API.

Uses the same pattern as alcf_iri_token.py but with NERSC-specific scopes.

Usage:
    python scripts/nersc_iri_token.py authenticate   # browser login
    python scripts/nersc_iri_token.py get_access_token
    python scripts/nersc_iri_token.py get_time_until_token_expiration
    python scripts/nersc_iri_token.py logout
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import time
import webbrowser

import globus_sdk
from globus_sdk.login_flows import LocalServerLoginFlowManager

try:
    from globus_sdk import GlobusAuthorizationParameters
except ImportError:
    from globus_sdk.gare import GlobusAuthorizationParameters


APP_NAME = "nersc_facility_api_app"
# Globus native app registered for both NERSC and ALCF IRI (from dingp's gist)
AUTH_CLIENT_ID = "fae5c579-490a-4d76-b6eb-d78f65caeb63"
# NERSC IRI resource server UUID
SCOPE_CLIENT_ID = "ed3e577d-f7f3-4639-b96e-ff5a8445d699"
SCOPE_STRING = f"https://auth.globus.org/scopes/{SCOPE_CLIENT_ID}/iri_api"
AUTH_SCOPES = ["openid", "profile", "email", "urn:globus:auth:scope:auth.globus.org:view_identities"]
TOKENS_PATH = pathlib.Path.home() / ".globus" / "app" / AUTH_CLIENT_ID / APP_NAME / "tokens.json"

# Credentials .env file. Resolve like the MCP servers (mcp/trinity_env.py) so a
# refreshed token lands in the SAME store the nersc-iri server reads:
#   1. $TRINITY_ENV_DIR/.env   — per-user store (Trinity multi-tenant / local switch)
#   2. $CLAUDE_ENV_FILE        — non-stripped contexts
#   3. <repo-root>/.env        — standalone CLI (bug fix: script lives in scripts/auth/,
#                                so repo root is parent.parent.PARENT, not parent.parent)
def _resolve_env_file() -> pathlib.Path:
    d = os.environ.get("TRINITY_ENV_DIR", "").strip()
    if d:
        return pathlib.Path(d) / ".env"
    f = os.environ.get("CLAUDE_ENV_FILE", "").strip()
    if f:
        return pathlib.Path(f)
    return pathlib.Path(__file__).resolve().parent.parent.parent / ".env"

ENV_FILE = _resolve_env_file()


class NERSCAuthError(Exception):
    """Raised when authentication state is missing or invalid."""


def _ensure_token_dir() -> None:
    TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)


def _build_client() -> globus_sdk.NativeAppAuthClient:
    return globus_sdk.NativeAppAuthClient(client_id=AUTH_CLIENT_ID, app_name=APP_NAME)


def _auth_params() -> GlobusAuthorizationParameters:
    # session_required_single_domain forces login via the NERSC identity provider,
    # which is required for the NERSC IRI to accept the resulting token.
    return GlobusAuthorizationParameters(
        required_scopes=[*AUTH_SCOPES, SCOPE_STRING],
        session_required_single_domain=["nersc.gov"],
        prompt="login",
    )


def _extract_token_data(token_response: globus_sdk.OAuthTokenResponse) -> dict:
    # Search other_tokens for the NERSC IRI scope (matches gist approach)
    raw = token_response.data
    for token_data in raw.get("other_tokens", []):
        if SCOPE_CLIENT_ID in token_data.get("scope", "") or SCOPE_STRING in token_data.get("scope", ""):
            result = dict(token_data)
            result["resource_server"] = SCOPE_CLIENT_ID
            result["scope_string"] = SCOPE_STRING
            return result
    # Fallback: by_resource_server lookup
    by_rs = token_response.by_resource_server
    if SCOPE_CLIENT_ID not in by_rs:
        raise NERSCAuthError(
            f"No token for resource server {SCOPE_CLIENT_ID}. "
            "Check that the NERSC IRI scope is correct and consent was granted."
        )
    token_data = dict(by_rs[SCOPE_CLIENT_ID])
    token_data["resource_server"] = SCOPE_CLIENT_ID
    token_data["scope_string"] = SCOPE_STRING
    return token_data


def _save_token_data(token_data: dict) -> None:
    _ensure_token_dir()
    TOKENS_PATH.write_text(json.dumps(token_data, indent=2, sort_keys=True), encoding="utf-8")


def _load_token_data() -> dict:
    if not TOKENS_PATH.is_file():
        raise NERSCAuthError(
            'No NERSC token found. Run "python scripts/nersc_iri_token.py authenticate" first.'
        )
    return json.loads(TOKENS_PATH.read_text(encoding="utf-8"))


def _update_env(key: str, value: str) -> None:
    """Update or add a key=value pair in the .env file, with a timestamp comment above it."""
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    timestamp_line = f"#{key} updated: {timestamp}"
    stamp_prefix = f"#{key} updated:"

    lines = []
    found = False
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            stripped = line.lstrip()
            if stripped.startswith(stamp_prefix):
                continue
            if stripped.startswith(f"export {key}=") or line.startswith(f"{key}="):
                lines.append(timestamp_line)
                lines.append(f"{key}={value}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(timestamp_line)
        lines.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(lines) + "\n")


def authenticate(force_reauth: bool = False) -> dict:
    """Launch browser login flow for NERSC IRI API."""
    if not force_reauth:
        try:
            token_data = get_token_data(force_refresh=False)
            token = token_data["access_token"]
            _update_env("NERSC_IRI_TOKEN", token)
            os.environ["NERSC_IRI_TOKEN"] = token
            expires = token_data.get("expires_at_seconds", 0)
            remaining = (expires - time.time()) / 3600
            print(f"Using existing NERSC token ({remaining:.1f}h remaining)")
            print(f"Token: {token[:20]}...")
            return token_data
        except NERSCAuthError:
            pass

    client = _build_client()
    flow = LocalServerLoginFlowManager(client, request_refresh_tokens=True)

    _original_open = webbrowser.open
    def _open_and_print(url, *args, **kwargs):
        print(f"\nOpen this URL in your browser to authenticate with NERSC:\n  {url}\n")
        return _original_open(url, *args, **kwargs)
    webbrowser.open = _open_and_print

    try:
        token_response = flow.run_login_flow(_auth_params())
    finally:
        webbrowser.open = _original_open

    token_data = _extract_token_data(token_response)
    _save_token_data(token_data)

    token = token_data["access_token"]
    _update_env("NERSC_IRI_TOKEN", token)
    os.environ["NERSC_IRI_TOKEN"] = token

    expires = token_data.get("expires_at_seconds", 0)
    remaining = (expires - time.time()) / 3600
    print(f"\nNERSC IRI token saved to {TOKENS_PATH}")
    print(f"NERSC_IRI_TOKEN written to {ENV_FILE}")
    print(f"Expires in {remaining:.1f} hours")
    print(f"Token: {token[:20]}...")
    return token_data


def _refresh_token_data(token_data: dict) -> dict:
    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        raise NERSCAuthError(
            'No refresh token. Run "python scripts/nersc_iri_token.py authenticate".'
        )
    client = _build_client()
    refreshed = client.oauth2_refresh_token(refresh_token)
    refreshed_data = _extract_token_data(refreshed)
    _save_token_data(refreshed_data)
    return refreshed_data


def get_token_data(force_refresh: bool = False) -> dict:
    token_data = _load_token_data()
    expires_at = token_data.get("expires_at_seconds", 0)
    if force_refresh or expires_at <= time.time() + 60:
        token_data = _refresh_token_data(token_data)
    return token_data


def get_access_token(force_refresh: bool = False) -> str:
    return get_token_data(force_refresh=force_refresh)["access_token"]


def get_time_until_token_expiration(units: str = "seconds") -> float:
    token_data = get_token_data(force_refresh=False)
    delta_t = token_data["expires_at_seconds"] - time.time()
    if units == "minutes":
        delta_t /= 60
    elif units == "hours":
        delta_t /= 3600
    return round(delta_t, 2)


def logout() -> None:
    if not TOKENS_PATH.is_file():
        print(f"No NERSC token file found at {TOKENS_PATH}")
        return
    TOKENS_PATH.unlink(missing_ok=True)
    print(f"NERSC token removed: {TOKENS_PATH}")


def ensure_valid() -> bool:
    """
    Non-interactive: refresh the cached token if close to expiry and write
    NERSC_IRI_TOKEN to .env. Returns True on success, False if no cached token
    is present or the refresh fails (caller should run `authenticate`).
    """
    try:
        token_data = get_token_data(force_refresh=False)
    except NERSCAuthError as exc:
        print(f"NERSC IRI ensure_valid failed: {exc}")
        return False
    except Exception as exc:
        print(f"NERSC IRI ensure_valid failed: {exc}")
        return False
    token = token_data["access_token"]
    _update_env("NERSC_IRI_TOKEN", token)
    os.environ["NERSC_IRI_TOKEN"] = token
    expires = token_data.get("expires_at_seconds", 0)
    remaining = (expires - time.time()) / 3600
    print(f"NERSC_IRI_TOKEN written to {ENV_FILE} ({remaining:.1f}h remaining)")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="NERSC IRI API token management")
    parser.add_argument(
        "action",
        nargs="?",
        default="ensure_valid",
        choices=["authenticate", "ensure_valid", "get_access_token", "get_time_until_token_expiration", "logout"],
        help="Action to perform (default: ensure_valid).",
    )
    parser.add_argument("--units", choices=["seconds", "minutes", "hours"], default="seconds")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--force-reauth", action="store_true")
    args = parser.parse_args()

    if args.action == "authenticate":
        authenticate(force_reauth=args.force_reauth)
    elif args.action == "ensure_valid":
        ok = ensure_valid()
        raise SystemExit(0 if ok else 1)
    elif args.action == "get_access_token":
        print(get_access_token(force_refresh=args.force_refresh))
    elif args.action == "get_time_until_token_expiration":
        print(get_time_until_token_expiration(args.units))
    elif args.action == "logout":
        logout()


if __name__ == "__main__":
    main()
