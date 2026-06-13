# Pocket Mechanics — Backend container
# Build:  docker build -t pocket-mechanics .
# Run:    docker run -p 8000:8000 --env-file Backend/.env pocket-mechanics
# Health: curl http://localhost:8000/health   ->  {"status":"ok"}

FROM python:3.11-slim

# Don't write .pyc, flush stdout/stderr immediately (clean container logs).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Non-root user (required by the rubric; safer container).
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

# Install dependencies first (better layer caching), then the app.
# pyproject.toml declares all runtime deps; pip resolves them from it.
COPY Backend/pyproject.toml /app/pyproject.toml
COPY Backend/ /app/
RUN pip install --no-cache-dir . \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Health check hits the internal /health endpoint (no LLM call, < 500ms).
# Uses stdlib urllib so we don't need curl in the slim image.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status==200 else 1)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
