FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (gcc for asyncpg, libpq-dev for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Health check: poll the /health endpoint every 30s.
# 3 retries before marking unhealthy; allow 40s start time for DB connections.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
