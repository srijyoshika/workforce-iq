# Multi-stage Dockerfile for WorkforceIQ FastAPI Backend

# Stage 1: Build & Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install OS build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Minimal Production Runtime
FROM python:3.11-slim AS runner

WORKDIR /app

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app:/app/backend
ENV PYTHONUNBUFFERED=1

# Create non-root application user
RUN groupadd -g 10001 workforce && \
    useradd -u 10001 -g workforce -s /bin/bash -m appuser && \
    chown -R appuser:workforce /app

# Copy application source code
COPY --chown=appuser:workforce . /app

USER appuser

EXPOSE 8000

# Health check probe against readiness endpoint
HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health/ready || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

