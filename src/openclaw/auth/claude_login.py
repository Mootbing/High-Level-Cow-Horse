"""Claude authentication via login credentials (not API key).

Supports multiple credential sources in priority order:
1. OpenClaw login credentials (~/.openclaw/credentials.json) - from `openclaw login`
2. Claude Code CLI credentials (~/.claude/) - if user has Claude Code installed
3. ANTHROPIC_API_KEY env var - fallback for backward compatibility
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import structlog
from anthropic import AsyncAnthropic

from openclaw.config import settings

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Credential paths
# ---------------------------------------------------------------------------

_DEFAULT_CREDS_DIR = Path.home() / ".openclaw"
_DEFAULT_CREDS_FILE = _DEFAULT_CREDS_DIR / "credentials.json"
_CLAUDE_CODE_DIR = Path.home() / ".claude"

# Module-level cached client so we don't re-create on every call
_cached_client: AsyncAnthropic | None = None
_cached_source: str | None = None


def _creds_path() -> Path:
    """Return the credentials file path, respecting config override."""
    if settings.OPENCLAW_CREDENTIALS_PATH:
        return Path(settings.OPENCLAW_CREDENTIALS_PATH)
    return _DEFAULT_CREDS_FILE


# ---------------------------------------------------------------------------
# Credential helpers
# ---------------------------------------------------------------------------


def get_credentials() -> dict:
    """Read credentials, trying multiple sources in priority order.

    Returns a dict with at minimum:
        {"source": str, "api_key": str}
    and optionally:
        {"oauth_token": str, "refresh_token": str, "expires_at": str}
    """
    # --- Source 1: OpenClaw login credentials ---
    creds_file = _creds_path()
    if creds_file.exists():
        try:
            data = json.loads(creds_file.read_text())
            token = data.get("oauth_token", "")
            if token:
                # Check expiry
                expires_at = data.get("expires_at")
                if expires_at:
                    try:
                        exp_dt = datetime.fromisoformat(expires_at)
                        if exp_dt.tzinfo is None:
                            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                        if exp_dt < datetime.now(timezone.utc):
                            log.warning(
                                "openclaw_credentials_expired",
                                expires_at=expires_at,
                            )
                            token = ""  # Clear so we fall through to other sources
                        else:
                            log.info("using_openclaw_login_credentials", path=str(creds_file))
                            return {
                                "source": "openclaw_login",
                                "api_key": token,
                                "oauth_token": token,
                                "refresh_token": data.get("refresh_token", ""),
                                "expires_at": expires_at,
                            }
                    except (ValueError, TypeError):
                        # Can't parse expiry — use anyway
                        pass

                # No expiry or unparseable — use the token
                if token:
                    log.info("using_openclaw_login_credentials", path=str(creds_file))
                    return {
                        "source": "openclaw_login",
                        "api_key": token,
                        "oauth_token": token,
                        "refresh_token": data.get("refresh_token", ""),
                        "expires_at": data.get("expires_at", ""),
                    }
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("openclaw_credentials_read_error", error=str(exc))

    # --- Source 2: Claude Code CLI credentials ---
    if _CLAUDE_CODE_DIR.is_dir():
        # Claude Code stores credentials in various locations; try common patterns
        for candidate in [
            _CLAUDE_CODE_DIR / "credentials.json",
            _CLAUDE_CODE_DIR / "auth.json",
            _CLAUDE_CODE_DIR / ".credentials",
        ]:
            if candidate.exists():
                try:
                    data = json.loads(candidate.read_text())
                    # Claude Code may store the key under different field names
                    token = (
                        data.get("oauth_token")
                        or data.get("api_key")
                        or data.get("sessionKey")
                        or data.get("token")
                        or ""
                    )
                    if token:
                        log.info(
                            "using_claude_code_credentials",
                            path=str(candidate),
                        )
                        return {
                            "source": "claude_code",
                            "api_key": token,
                            "oauth_token": token,
                            "refresh_token": data.get("refresh_token", ""),
                            "expires_at": data.get("expires_at", ""),
                        }
                except (json.JSONDecodeError, OSError) as exc:
                    log.debug("claude_code_creds_skip", path=str(candidate), error=str(exc))

    # --- Source 3: Environment variable fallback ---
    env_key = settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")
    if env_key:
        log.info("using_anthropic_api_key_fallback")
        return {
            "source": "api_key_env",
            "api_key": env_key,
        }

    # Nothing found
    log.error("no_anthropic_credentials_found")
    return {"source": "none", "api_key": ""}


def save_credentials(
    token: str,
    refresh_token: str | None = None,
    expires_at: str | None = None,
) -> None:
    """Save OAuth credentials to ~/.openclaw/credentials.json."""
    creds_file = _creds_path()
    creds_file.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "oauth_token": token,
        "refresh_token": refresh_token or "",
        "expires_at": expires_at or "",
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    creds_file.write_text(json.dumps(data, indent=2) + "\n")
    # Restrict permissions to owner only
    creds_file.chmod(0o600)
    log.info("credentials_saved", path=str(creds_file))


def delete_credentials() -> bool:
    """Remove the stored credentials file. Returns True if file existed."""
    creds_file = _creds_path()
    if creds_file.exists():
        creds_file.unlink()
        log.info("credentials_deleted", path=str(creds_file))
        return True
    return False


def get_auth_status() -> dict:
    """Return a summary of the current authentication status."""
    creds = get_credentials()
    source = creds.get("source", "none")
    result = {
        "authenticated": source != "none",
        "source": source,
    }
    if creds.get("expires_at"):
        result["expires_at"] = creds["expires_at"]
        try:
            exp_dt = datetime.fromisoformat(creds["expires_at"])
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            result["expired"] = exp_dt < datetime.now(timezone.utc)
        except (ValueError, TypeError):
            result["expired"] = None
    else:
        result["expired"] = False

    return result


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------


async def get_claude_client() -> AsyncAnthropic:
    """Return an AsyncAnthropic client using the best available credentials.

    The client is cached at module level so repeated calls reuse the same
    connection pool. Call ``reset_client()`` if credentials change.
    """
    global _cached_client, _cached_source

    if _cached_client is not None:
        return _cached_client

    creds = get_credentials()
    api_key = creds.get("api_key", "")
    source = creds.get("source", "none")

    if not api_key:
        raise RuntimeError(
            "No Anthropic credentials found. Run `openclaw login` or set ANTHROPIC_API_KEY."
        )

    _cached_client = AsyncAnthropic(api_key=api_key)
    _cached_source = source
    log.info("claude_client_created", credential_source=source)
    return _cached_client


def reset_client() -> None:
    """Clear the cached client so the next ``get_claude_client()`` re-reads credentials."""
    global _cached_client, _cached_source
    _cached_client = None
    _cached_source = None
