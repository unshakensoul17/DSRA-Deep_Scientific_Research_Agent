#!/bin/bash
set -e

echo "Running database migrations..."
PYTHONPATH=/workspace alembic upgrade head

echo "Starting application server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
