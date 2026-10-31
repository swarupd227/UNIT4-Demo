FROM python:3.13-slim

WORKDIR /build
COPY apps/api/pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir ".[dev]"

WORKDIR /workspace/apps/api
