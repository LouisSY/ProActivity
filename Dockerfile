# syntax=docker/dockerfile:1

FROM --platform=linux/amd64 ghcr.io/astral-sh/uv:debian

# Fix for `ImportError: libGL.so.1: cannot open shared object file: No such file or directory`
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update && apt-get --no-install-recommends install -y libgl1 libglib2.0-0

WORKDIR /app

ENV UV_LINK_MODE=copy
ENV UV_PYTHON_CACHE_DIR=/root/.cache/uv/python
ENV PYTHONPATH=/app/src:/app

COPY uv.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

COPY . .

EXPOSE 8050 2000 2001 2002 8000 8001 8002

# Default to bash for debugging
CMD ["/bin/bash"]
