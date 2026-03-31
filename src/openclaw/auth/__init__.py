"""OpenClaw authentication — Claude OAuth login instead of raw API keys."""

from openclaw.auth.claude_login import get_claude_client, get_credentials

__all__ = ["get_claude_client", "get_credentials"]
