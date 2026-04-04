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

# Replace local loopback URLs in Python files inside container source
RUN find /app/src -type f -name "*.py" -print0 | \
    xargs -0 sed -E -i \
    -e 's#http://127\.0\.0\.1:([0-9]+)#http://host.docker.internal:\1#g' \
    -e 's#http://localhost:([0-9]+)#http://host.docker.internal:\1#g'


EXPOSE 8050 2002 8000 8001 8002

# Default to bash for debugging
CMD ["/bin/bash"]
