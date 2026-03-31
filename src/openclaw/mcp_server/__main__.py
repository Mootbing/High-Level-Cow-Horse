"""MCP server entry point. Run with: python -m openclaw.mcp_server"""

from openclaw.mcp_server.server import mcp

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
