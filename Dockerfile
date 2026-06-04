# ==========================================
# STAGE 1: Secure Dependency Compilation Layer
# ==========================================
FROM python:3.11-alpine AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk add --no-cache gcc musl-dev postgresql-dev libffi-dev

# SECURITY PATCH: Force upgrade wheel past the file path traversal threshold (CVE-2026-24049)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel==0.46.2

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# STAGE 2: Distroless Zero-Vulnerability Runtime
# ==========================================
# Completely eliminates BusyBox (CVE-2025-60876) by stripping the OS shell environment layer
FROM gcr.io/distroless/python3-debian12:latest AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PATH="/root/.local/bin:$PATH"

# Pull the runtime PostgreSQL shared library objects from alpine builder to satisfy driver links
COPY --from=builder /usr/lib/libpq.so.5* /usr/lib/

# Pull compiled site-packages from the builder layer
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# Ingest explicit system code components
COPY api/ /app/api/
COPY workers/ /app/workers/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini

EXPOSE 8000

# Invoke via direct python binary module execution to bypass missing shell contexts securely
CMD ["-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
