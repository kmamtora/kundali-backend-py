.PHONY: install format lint typecheck test test-cov migrate migrate-create dev worker beat docker-build docker-up docker-down clean help

help:
	@echo "Available commands:"
	@echo "  make install        - Install dependencies with UV"
	@echo "  make format         - Format code with Ruff"
	@echo "  make lint           - Lint code with Ruff"
	@echo "  make typecheck      - Type check with MyPy"
	@echo "  make test           - Run tests with pytest"
	@echo "  make test-cov       - Run tests with coverage"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create new migration (use MSG='description')"
	@echo "  make dev            - Run development server"
	@echo "  make worker         - Run Celery worker"
	@echo "  make beat           - Run Celery beat scheduler"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-up      - Start Docker Compose services"
	@echo "  make docker-down    - Stop Docker Compose services"
	@echo "  make clean          - Clean up cache and temporary files"

install:
	uv sync

format:
	uv run ruff format .

lint:
	uv run ruff check . --fix

typecheck:
	uv run mypy app/

test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

migrate:
	uv run alembic upgrade head

migrate-create:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: Please provide a migration message using MSG='description'"; \
		exit 1; \
	fi
	uv run alembic revision --autogenerate -m "$(MSG)"

dev:
	uv run uvicorn app.cmd.main:app --reload --host 0.0.0.0 --port 8000

worker:
	uv run celery -A app.tasks.celery_app worker --loglevel=info

beat:
	uv run celery -A app.tasks.celery_app beat --loglevel=info

docker-build:
	docker build -t enterprise-api:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
