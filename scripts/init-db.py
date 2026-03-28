#!/usr/bin/env python3
"""Initialize the database: run migrations and create initial data."""
import asyncio
import subprocess
import sys


async def main():
    # Run alembic migrations
    print("Running database migrations...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Migration failed: {result.stderr}")
        sys.exit(1)
    print("Migrations complete.")

    # Initialize Redis streams
    print("Initializing Redis streams...")
    import redis.asyncio as redis
    from openclaw.config import settings
    from openclaw.queue.streams import init_streams

    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    await init_streams(r)
    await r.aclose()
    print("Redis streams initialized.")

    print("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())
