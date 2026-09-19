FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY apps /app/apps
COPY packages /app/packages
COPY scripts /app/scripts
COPY alembic.ini /app/alembic.ini

RUN pip install --upgrade pip && pip install . && chmod +x /app/scripts/start_api.sh

RUN useradd --create-home --shell /usr/sbin/nologin appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 10000

CMD ["/app/scripts/start_api.sh"]
