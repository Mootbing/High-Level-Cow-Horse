"""Run the audit worker (poll loop only — no HTTP server)."""

import asyncio

from openclaw.audit_worker.worker import run_audit_worker

if __name__ == "__main__":
    asyncio.run(run_audit_worker())
