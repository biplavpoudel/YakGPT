FROM python:3.12-slim-trixie

# 1. Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 2. We set up the explicit non-root user
RUN useradd -m -u 1000 user
ENV HOME=/home/user
WORKDIR /app

# 3. We ensure our user owns the app dir
RUN chown -R user:user /app

# 4.  We switch to the HF user before running any further installations
USER user

# 5. Bring in the uv binary (installed to the user's bin pathway)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /home/user/.local/bin/

# 6. Copy dependency definitions
COPY --chown=user:user pyproject.toml uv.lock ./

# 7. Sync all dependencies from your lockfile into /app/.venv
RUN /home/user/.local/bin/uv sync --frozen --no-install-project --python 3.12

# 8. Download TTS model for narration and run only once when Hugging Face builds the container, never during gameplay!
RUN mkdir -p /app/models && \
    wget /app/models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx && \
    wget /app/models/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

# 9. We tell the python backend where our model lives
ENV KOKORO_MODEL_PATH="/app/models/kokoro-v1.0.onnx" \
    KOKORO_VOICES_PATH="/app/models/voices-v1.0.bin" \
    PATH="/app/.venv/bin:/home/user/.local/bin:$PATH"

# 10. We copy the rest of your application code
COPY --chown=user:user . .

#  11. 'python' now naturally refers to the venv python, which has all our dependencies
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]