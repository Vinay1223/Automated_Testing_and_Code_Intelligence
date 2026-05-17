FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates docker.io \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages packages
COPY apps/api apps/api
RUN uv sync --frozen --no-dev

EXPOSE 8000
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "codeintel_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
