# Build stage
FROM python:3.10-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY reversi_backend ./reversi_backend
COPY main.py ./

# Copy Alembic files for database migrations
COPY alembic ./alembic
COPY alembic.ini ./

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Default environment variables for production
ENV HOST=0.0.0.0
ENV PORT=8000
ENV RELOAD=false
ENV FRONTEND_ORIGINS=[]

# Expose port
EXPOSE 8000

# Run migrations and start the application
CMD ["sh", "-c", "alembic upgrade head && python main.py"]
