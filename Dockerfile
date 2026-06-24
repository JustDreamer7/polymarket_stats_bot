FROM python:3.11-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app
RUN apk add --no-cache postgresql-libs && \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev
RUN pip3 install uv \
    && python3 -m uv venv .venv

COPY pyproject.toml uv.lock ./
RUN python3 -m uv sync --active --no-dev --no-install-project

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini main.py healthcheck.py ./

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "main.py"]
