FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv --no-cache-dir

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock* ./

# Install production deps only
RUN uv sync --frozen --no-dev

# Copy application source
COPY app/ ./app/

# Cloud Run passes PORT env var -- default 8080 if not set
ENV PORT=8080

CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --timeout-keep-alive 120"]
