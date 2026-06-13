.PHONY: help setup test unit graph integration-test eval lint run-api compose-up compose-down health security-test performance-smoke

PY ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-18s %s\n", $$1, $$2}'

setup: ## Create venv and install package in editable mode with dev extras
	$(PY) -m venv $(VENV)
	$(PIP) install -U pip >/dev/null
	$(PIP) install -e ".[dev]"

test: unit ## Alias: run unit + graph tests (no external services)
	@true

unit: ## Run unit tests (no external services)
	$(PYTEST) -m "unit or not (integration or external)" tests

graph: ## Run LangGraph path tests (mocks)
	$(PYTEST) -m graph tests

security-test: ## Run security tests
	$(PYTEST) -m security tests

performance-smoke: ## Run performance smoke tests
	$(PYTEST) -m performance tests

eval: ## Run RAG golden evaluation suite
	$(PYTEST) -m rag_quality tests

integration-test: ## Run integration tests (require Docker services)
	$(PYTEST) -m integration tests

lint: ## Lint with ruff
	$(VENV)/bin/ruff check src tests

run-api: ## Run FastAPI service (mock profile)
	$(VENV)/bin/uvicorn voice_rag_agents.service.api:app --reload

compose-up: ## Start local stack (Milvus/Ollama/Open WebUI/API)
	docker compose up -d

compose-down: ## Stop local stack
	docker compose down

health: ## Run healthcheck script
	bash scripts/healthcheck.sh
