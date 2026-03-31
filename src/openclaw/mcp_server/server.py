"""Clarmi Design Studio MCP Server — exposes all tools for the OpenClaw agent."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("clarmi-tools")

# Import all tool modules to register them with the server
import openclaw.mcp_server.tools.scraping  # noqa: F401
import openclaw.mcp_server.tools.projects  # noqa: F401
import openclaw.mcp_server.tools.prospects  # noqa: F401
import openclaw.mcp_server.tools.design  # noqa: F401
import openclaw.mcp_server.tools.engineering  # noqa: F401
import openclaw.mcp_server.tools.qa  # noqa: F401
import openclaw.mcp_server.tools.email  # noqa: F401
import openclaw.mcp_server.tools.research  # noqa: F401
import openclaw.mcp_server.tools.learning  # noqa: F401
