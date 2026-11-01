FROM python:3.13-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-liberation

WORKDIR /build
COPY apps/api/pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip

# Local development: the repository is mounted in by docker-compose.yml.
FROM base AS dev
RUN pip install --no-cache-dir ".[dev,azure]"
WORKDIR /workspace/apps/api

# Azure: everything is in the image. The seed job replaces data/generated, so it owns data itself.
FROM base AS production
RUN pip install --no-cache-dir ".[azure]"
COPY apps/api /app/apps/api
COPY engines /app/engines
COPY data /app/data
RUN useradd --create-home --uid 10001 studio && chown studio /app/data
ENV PYTHONPATH=/app:/app/apps/api
WORKDIR /app/apps/api
USER 10001
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
