FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (needed for frontend build + Next.js generation)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pre-install frontend deps (cached unless package.json changes)
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci

# Copy everything and install Python
COPY . .
RUN pip install --no-cache-dir .

# Build frontend (after COPY so source is present)
RUN cd frontend && npm run build

# Install playwright browsers for QA agent
RUN playwright install chromium && playwright install-deps chromium

EXPOSE 8000

CMD ["uvicorn", "openclaw.main:app", "--host", "0.0.0.0", "--port", "8000"]
