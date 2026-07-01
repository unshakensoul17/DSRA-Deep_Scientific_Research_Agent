# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
ENV POETRY_VERSION=1.8.3
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml ./

# Disable virtualenvs so poetry installs directly to the global python system site-packages
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-directory --only main

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

# Expose port
EXPOSE 8000

# Create non-root user for execution
RUN useradd -u 8888 appuser && chown -R appuser:appuser /workspace
USER appuser

# Start application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
