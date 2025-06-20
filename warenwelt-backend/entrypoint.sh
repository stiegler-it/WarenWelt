#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start Uvicorn server
# The CMD from Dockerfile is not used when ENTRYPOINT is a script like this.
# So, we need to exec the uvicorn command here.
echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
