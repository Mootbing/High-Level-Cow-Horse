"""OpenClaw CLI for authentication and management.

Usage:
  openclaw login     - Authenticate with Anthropic (OAuth device flow)
  openclaw logout    - Remove stored credentials
  openclaw status    - Check authentication status
  openclaw run       - Start the skill runner
"""

from __future__ import annotations

import argparse
import getpass
import json
import sys
import time

import httpx

from openclaw.auth.claude_login import (
    delete_credentials,
    get_auth_status,
    save_credentials,
)

# ---------------------------------------------------------------------------
# Anthropic OAuth device-flow constants
# ---------------------------------------------------------------------------

_ANTHROPIC_DEVICE_AUTH_URL = "https://console.anthropic.com/oauth/device/code"
_ANTHROPIC_TOKEN_URL = "https://console.anthropic.com/oauth/token"
_ANTHROPIC_CLIENT_ID = "openclaw-cli"
_POLL_INTERVAL_S = 5
_MAX_POLL_S = 300  # 5 minutes


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def login() -> None:
    """Authenticate with Anthropic.

    Attempts OAuth device flow first. If the device endpoint is not available
    (e.g., Anthropic hasn't enabled it yet), falls back to prompting the user
    to paste an API key or session token directly.
    """
    print("OpenClaw — Authenticate with Anthropic\n")

    # --- Try OAuth device flow ---
    try:
        _device_flow_login()
        return
    except (httpx.HTTPStatusError, httpx.ConnectError, KeyError) as exc:
        print(f"\nOAuth device flow unavailable ({type(exc).__name__}). Falling back to manual entry.\n")

    # --- Fallback: manual token / API key entry ---
    _manual_token_login()


def _device_flow_login() -> None:
    """Execute the OAuth 2.0 device authorization flow."""
    with httpx.Client(timeout=30) as http:
        # Step 1: Request a device code
        resp = http.post(
            _ANTHROPIC_DEVICE_AUTH_URL,
            json={"client_id": _ANTHROPIC_CLIENT_ID, "scope": "api"},
        )
        resp.raise_for_status()
        data = resp.json()

        device_code: str = data["device_code"]
        user_code: str = data["user_code"]
        verification_uri: str = data.get("verification_uri", "https://console.anthropic.com/device")
        interval: int = data.get("interval", _POLL_INTERVAL_S)

        print(f"  1. Open this URL in your browser:\n\n     {verification_uri}\n")
        print(f"  2. Enter this code when prompted:\n\n     {user_code}\n")
        print("  Waiting for authorization...\n")

        # Step 2: Poll for the token
        deadline = time.monotonic() + _MAX_POLL_S
        while time.monotonic() < deadline:
            time.sleep(interval)
            token_resp = http.post(
                _ANTHROPIC_TOKEN_URL,
                json={
                    "client_id": _ANTHROPIC_CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
            )
            if token_resp.status_code == 200:
                token_data = token_resp.json()
                save_credentials(
                    token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token"),
                    expires_at=token_data.get("expires_at"),
                )
                print("  Authenticated successfully! Credentials saved.\n")
                return

            # Handle pending / slow-down / errors
            body = token_resp.json() if token_resp.headers.get("content-type", "").startswith("application/json") else {}
            error = body.get("error", "")
            if error == "authorization_pending":
                continue
            elif error == "slow_down":
                interval = min(interval + 2, 30)
                continue
            elif error in ("expired_token", "access_denied"):
                print(f"  Authorization failed: {error}")
                sys.exit(1)
            else:
                # Unknown error — fall through
                token_resp.raise_for_status()

        print("  Timed out waiting for authorization.")
        sys.exit(1)


def _manual_token_login() -> None:
    """Prompt the user to paste an API key or session token."""
    print("Enter your Anthropic API key or session token.")
    print("(You can get an API key at https://console.anthropic.com/settings/keys)\n")
    token = getpass.getpass("Token: ").strip()
    if not token:
        print("No token entered. Aborting.")
        sys.exit(1)

    # Quick validation: try a lightweight API call
    print("  Verifying credentials...")
    try:
        with httpx.Client(timeout=15) as http:
            resp = http.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": token,
                    "anthropic-version": "2023-06-01",
                },
            )
            if resp.status_code in (200, 403):
                # 200 = valid key; 403 = valid key but no model-list permission
                save_credentials(token=token)
                print("  Authenticated successfully! Credentials saved.\n")
                return
            else:
                print(f"  Warning: API returned status {resp.status_code}. Saving token anyway.\n")
                save_credentials(token=token)
    except httpx.HTTPError:
        print("  Could not verify token (network error). Saving it anyway.\n")
        save_credentials(token=token)


def logout() -> None:
    """Remove stored credentials."""
    removed = delete_credentials()
    if removed:
        print("Logged out. Credentials removed.")
    else:
        print("No credentials file found — already logged out.")


def status() -> None:
    """Show current authentication status."""
    info = get_auth_status()
    print("OpenClaw — Authentication Status\n")
    if info["authenticated"]:
        source_labels = {
            "openclaw_login": "OpenClaw login (~/.openclaw/credentials.json)",
            "claude_code": "Claude Code CLI (~/.claude/)",
            "api_key_env": "ANTHROPIC_API_KEY environment variable",
        }
        label = source_labels.get(info["source"], info["source"])
        print(f"  Source:  {label}")
        if info.get("expires_at"):
            print(f"  Expires: {info['expires_at']}")
            if info.get("expired"):
                print("  Status:  EXPIRED — run `openclaw login` to refresh")
            else:
                print("  Status:  Active")
        else:
            print("  Status:  Active (no expiry)")
    else:
        print("  Not authenticated.")
        print("  Run `openclaw login` or set ANTHROPIC_API_KEY.")


def run() -> None:
    """Start the OpenClaw skill runner."""
    try:
        from openclaw.runtime.skill_runner import main as runner_main
        runner_main()
    except ImportError as exc:
        print(f"Could not import skill runner: {exc}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for the ``openclaw`` command."""
    parser = argparse.ArgumentParser(
        prog="openclaw",
        description="OpenClaw — AI-powered multi-agent skill runner",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("login", help="Authenticate with Anthropic (OAuth device flow)")
    subparsers.add_parser("logout", help="Remove stored credentials")
    subparsers.add_parser("status", help="Check authentication status")
    subparsers.add_parser("run", help="Start the skill runner")

    args = parser.parse_args()

    commands = {
        "login": login,
        "logout": logout,
        "status": status,
        "run": run,
    }

    handler = commands.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(0)
    handler()


if __name__ == "__main__":
    main()
