FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# - UV_COMPILE_BYTECODE=1: Compiles .py to .pyc for faster container startup
# - UV_LINK_MODE=copy: Prevents hardlink warnings when using cache mounts
# - UV_PYTHON_DOWNLOADS=0: Forces uv to use the base image's system Python
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable



FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS runtime

RUN groupadd --system --gid 10001 appgroup && \
    useradd --system --uid 10001 --gid appgroup --create-home appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appgroup /app /app

# - PYTHONUNBUFFERED=1: Send Python output straight to the terminal without being first buffered.
# - PYTHONDONTWRITEBYTECODE=1: prevent Python from writing bytecode into __pycache__
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 8080

CMD ["fastapi", "run", "src/app/main.py", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
