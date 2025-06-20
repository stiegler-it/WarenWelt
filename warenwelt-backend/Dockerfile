# Stage 1: Build/Install dependencies
FROM python:3.9-slim as builder

WORKDIR /app

# Install system dependencies that might be needed by some Python packages
# e.g., for psycopg2 (if using PostgreSQL later) build tools might be needed
# For SQLite and current requirements, this might be minimal.
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
#    && rm -rf /var/lib/apt/lists/*

# Set environment variables to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Poetry (optional, if you prefer to use poetry for dependency management)
# RUN pip install poetry
# COPY poetry.lock pyproject.toml /app/
# RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

# Using requirements.txt
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# Stage 2: Final image
FROM python:3.9-slim

WORKDIR /app

# Copy installed wheels from builder stage and install them
COPY --from=builder /app/wheels /wheels/
RUN pip install --no-cache /wheels/*

# Copy the rest of the application code
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable for database URL (can be overridden in docker-compose)
ENV DATABASE_URL="sqlite:///./test.db"
# It's better to set sensitive keys via docker-compose .env file
# ENV SECRET_KEY="your_very_strong_and_secret_key_here_please_change_me"
ENV ALEMBIC_CONFIG="alembic.ini"

# Create a non-root user to run the application (optional but good practice)
# RUN addgroup -S appgroup && adduser -S appuser -G appgroup
# USER appuser

# Command to run migrations and then start the Uvicorn server
# We'll use an entrypoint script to handle this logic.
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# Default command if entrypoint.sh is not used or for direct uvicorn start
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
