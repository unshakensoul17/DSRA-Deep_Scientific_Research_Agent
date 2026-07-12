# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final runtime image
FROM python:3.12-slim AS runner

WORKDIR /workspace

# Install runtime dependencies (e.g. libpq for pg database, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed site-packages and binaries from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY app/ /workspace/app/
COPY migrations/ /workspace/migrations/
COPY alembic.ini /workspace/alembic.ini
COPY entrypoint.sh /workspace/entrypoint.sh

# Expose port
EXPOSE 8000

# Create non-root user for execution
RUN useradd -u 8888 appuser \
    && chown -R appuser:appuser /workspace \
    && chmod +x /workspace/entrypoint.sh
USER appuser

# Start: run migrations then launch uvicorn
CMD ["/workspace/entrypoint.sh"]
