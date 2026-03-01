# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:debian

# Fix for `ImportError: libGL.so.1: cannot open shared object file: No such file or directory`
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update && apt-get --no-install-recommends install -y libgl1

WORKDIR /app

ENV UV_LINK_MODE=copy
ENV UV_PYTHON_CACHE_DIR=/root/.cache/uv/python

COPY uv.lock pyproject.toml .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

COPY . .

EXPOSE 8050

CMD ["uv", "run", "python", "src/ProVoice/main.py", "participantid=001", "environment=city", "secondary_task=none", "functionname='Adjust seat positioning'", "modeltype=combined", "state_model=xlstm", "w_fcd=0.7"]
