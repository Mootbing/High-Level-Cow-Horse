"""Entry point: python -m openclaw.api"""

import uvicorn

from openclaw.config import settings

uvicorn.run(
    "openclaw.api.app:app",
    host="0.0.0.0",
    port=settings.API_PORT,
    reload=settings.DEBUG,
)
