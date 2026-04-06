"""Run the audit worker service."""

import uvicorn

from openclaw.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "openclaw.audit_worker.app:app",
        host="0.0.0.0",
        port=settings.AUDIT_WORKER_PORT,
        reload=settings.DEBUG,
    )
