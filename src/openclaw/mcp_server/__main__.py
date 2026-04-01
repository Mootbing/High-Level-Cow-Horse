"""MCP server entry point. Run with: python -m openclaw.mcp_server"""

import sys
import logging

from openclaw.mcp_server.server import mcp

logger = logging.getLogger("openclaw.mcp_server")

def main():
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception("mcp_server_crashed", exc_info=e)
        sys.exit(1)

if __name__ == "__main__":
    main()
