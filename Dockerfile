# Dockerfile for voice_rag_agents API service.
FROM python:3.12-slim

WORKDIR /app

# System deps for healthcheck curl
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir ".[api,graph,milvus]"

EXPOSE 8088

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8088/health || exit 1

CMD ["uvicorn", "voice_rag_agents.service.api:app", "--host", "0.0.0.0", "--port", "8088"]
