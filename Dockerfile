# ─────────────────────────────────────────────────────────────
# Conut Ops AI  –  Backend API
# Build: docker build -t conut-api .
# Run:   docker run -p 8000:8000 --env-file .env conut-api
# ─────────────────────────────────────────────────────────────

# ── Stage 1: dependency installer ────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools needed by some packages (scikit-learn, numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: lean runtime image ──────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY main.py          ./main.py
COPY telegram_bot.py  ./telegram_bot.py
COPY app/             ./app/
COPY data/            ./data/

# Env defaults (overridden at runtime via --env-file or Cloud Run env vars)
ENV PORT=8000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Switch to non-root
USER appuser

EXPOSE 8000

# Cloud Run injects $PORT; uvicorn reads it via main.py's __main__ block
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
