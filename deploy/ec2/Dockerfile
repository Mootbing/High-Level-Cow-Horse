# =============================================================================
# OpenClaw — Production Dockerfile (EC2 Single Instance)
#
# Builds the unified image used by both the `api` and `skills` services.
#   - api:    CMD uvicorn openclaw.main:app ...
#   - skills: CMD python -m openclaw.runtime.skill_runner --all
# =============================================================================
FROM python:3.12-slim AS base

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ---------------------------------------------------------------------------
# System dependencies
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Node.js 22 (for engineer skill npm/Next.js builds + frontend build)
# ---------------------------------------------------------------------------
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Create non-root user
# ---------------------------------------------------------------------------
RUN groupadd -r openclaw && useradd -r -g openclaw -m -d /home/openclaw openclaw

WORKDIR /app

# ---------------------------------------------------------------------------
# Frontend dependencies (cached layer — only rebuilt when package.json changes)
# ---------------------------------------------------------------------------
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci --no-audit --no-fund

# ---------------------------------------------------------------------------
# Python dependencies (cached layer — only rebuilt when pyproject.toml changes)
# ---------------------------------------------------------------------------
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

# ---------------------------------------------------------------------------
# Copy full project (skills, frontend source, clawdbot, configs, etc.)
# ---------------------------------------------------------------------------
COPY . .

# ---------------------------------------------------------------------------
# Build frontend
# ---------------------------------------------------------------------------
RUN cd frontend && npm run build

# ---------------------------------------------------------------------------
# Install Playwright + Chromium for QA skill
# ---------------------------------------------------------------------------
RUN playwright install chromium && playwright install-deps chromium

# ---------------------------------------------------------------------------
# Create credentials directory + set permissions
# ---------------------------------------------------------------------------
RUN mkdir -p /home/openclaw/.openclaw \
    && chown -R openclaw:openclaw /home/openclaw/.openclaw \
    && mkdir -p /data/projects \
    && chown -R openclaw:openclaw /data/projects \
    && chown -R openclaw:openclaw /app

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
EXPOSE 8000

USER openclaw

# Default: run the API server. Override in docker-compose for skills container.
CMD ["uvicorn", "openclaw.main:app", "--host", "0.0.0.0", "--port", "8000"]
