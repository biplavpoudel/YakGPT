FROM python:3.12-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

# 1. Sync all dependencies from your lockfile into /app/.venv
RUN uv sync --frozen --no-install-project --python 3.12

# 2. Make sure the container uses the virtual environment automatically
ENV PATH="/app/.venv/bin:$PATH"

# Copy the rest of your application code
COPY . .

# 'python' now naturally refers to the venv python, which has all your dependencies
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]