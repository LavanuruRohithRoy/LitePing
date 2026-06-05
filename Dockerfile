# ==========================================
# STAGE 1: Secure Dependency Compilation Layer
# ==========================================
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential libpq-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# SECURITY PATCH: Force upgrade wheel past the file path traversal threshold (CVE-2026-24049)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel==0.46.2

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# STAGE 2: Runtime Layer
# ==========================================
FROM python:3.11-slim-bookworm AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PATH="/root/.local/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Pull compiled site-packages from the builder layer
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# Ingest explicit system code components
COPY api/ /app/api/
COPY workers/ /app/workers/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
