.PHONY: help install dev test clean format lint type-check migrate docker-up docker-down docker-logs

# Default target
help:
	@echo "HyperToQ Backend - Makefile Commands"
	@echo "===================================="
	@echo "install       - Install dependencies with Poetry"
	@echo "dev           - Run development server"
	@echo "test          - Run tests"
	@echo "test-cov      - Run tests with coverage"
	@echo "format        - Format code with Black"
	@echo "lint          - Lint code with Ruff"
	@echo "type-check    - Type check with MyPy"
	@echo "migrate       - Run database migrations"
	@echo "migrate-create - Create new migration"
	@echo "docker-up     - Start Docker services"
	@echo "docker-down   - Stop Docker services"
	@echo "docker-logs   - View Docker logs"
	@echo "celery-worker - Start Celery worker"
	@echo "celery-beat   - Start Celery beat"
	@echo "clean         - Remove cache and build files"

# Install dependencies
install:
	poetry install

# Run development server
dev:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	poetry run pytest

# Run tests with coverage
test-cov:
	poetry run pytest --cov=app --cov-report=html --cov-report=term

# Format code
format:
	poetry run black app/ tests/
	poetry run ruff check app/ tests/ --fix

# Lint code
lint:
	poetry run ruff check app/ tests/

# Type checking
type-check:
	poetry run mypy app/

# Run database migrations
migrate:
	poetry run alembic upgrade head

# Create new migration
migrate-create:
	@read -p "Enter migration message: " msg; \
	poetry run alembic revision --autogenerate -m "$$msg"

# Start Docker services
docker-up:
	docker-compose up -d

# Stop Docker services
docker-down:
	docker-compose down

# View Docker logs
docker-logs:
	docker-compose logs -f

# Start Celery worker
celery-worker:
	poetry run celery -A app.core.celery_app worker --loglevel=info

# Start Celery beat
celery-beat:
	poetry run celery -A app.core.celery_app beat --loglevel=info

# Clean cache and build files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
