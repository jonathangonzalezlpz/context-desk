# syntax=docker/dockerfile:1
FROM python:3.12-slim as builder

# Instalar uv rapido y reproducible
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml .

# Instalar dependencias
RUN uv pip install --system --no-cache-dir .

FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY backend/src /app/backend/src

# Segurizar contenedor
RUN useradd -m appuser && chown -R appuser /app
USER appuser

CMD ["uvicorn", "backend.src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
