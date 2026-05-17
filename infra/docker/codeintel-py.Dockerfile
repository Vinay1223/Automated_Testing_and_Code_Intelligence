FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN useradd -u 1000 -m sandbox \
 && pip install --no-cache-dir \
      pytest==9.0.3 \
      hypothesis==6.112.1 \
      pydantic==2.9.2

USER sandbox
WORKDIR /repo

ENTRYPOINT ["pytest"]
