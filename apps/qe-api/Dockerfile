FROM python:3.13-slim

# git reads the module's history; the rest is Python.
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY apps/qe-api/pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir ".[dev]"

# The repository is mounted in by docker-compose.qe.yml.
WORKDIR /workspace/apps/qe-api
