# HyperToQ Backend - PowerShell Commands
# Windows-friendly commands for development

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "HyperToQ Backend - PowerShell Commands" -ForegroundColor Cyan
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\commands.ps1 <command>" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Green
    Write-Host "  install       - Install dependencies with Poetry"
    Write-Host "  dev           - Run development server"
    Write-Host "  test          - Run tests"
    Write-Host "  test-cov      - Run tests with coverage"
    Write-Host "  format        - Format code with Black"
    Write-Host "  lint          - Lint code with Ruff"
    Write-Host "  type-check    - Type check with MyPy"
    Write-Host "  migrate       - Run database migrations"
    Write-Host "  docker-up     - Start Docker services"
    Write-Host "  docker-down   - Stop Docker services"
    Write-Host "  docker-logs   - View Docker logs"
    Write-Host "  celery-worker - Start Celery worker"
    Write-Host "  celery-beat   - Start Celery beat"
    Write-Host "  clean         - Remove cache files"
    Write-Host ""
}

switch ($Command) {
    "install" {
        Write-Host "Installing dependencies..." -ForegroundColor Green
        poetry install
    }
    "dev" {
        Write-Host "Starting development server..." -ForegroundColor Green
        poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    }
    "test" {
        Write-Host "Running tests..." -ForegroundColor Green
        poetry run pytest
    }
    "test-cov" {
        Write-Host "Running tests with coverage..." -ForegroundColor Green
        poetry run pytest --cov=app --cov-report=html --cov-report=term
    }
    "format" {
        Write-Host "Formatting code..." -ForegroundColor Green
        poetry run black app/ tests/
        poetry run ruff check app/ tests/ --fix
    }
    "lint" {
        Write-Host "Linting code..." -ForegroundColor Green
        poetry run ruff check app/ tests/
    }
    "type-check" {
        Write-Host "Type checking..." -ForegroundColor Green
        poetry run mypy app/
    }
    "migrate" {
        Write-Host "Running migrations..." -ForegroundColor Green
        poetry run alembic upgrade head
    }
    "docker-up" {
        Write-Host "Starting Docker services..." -ForegroundColor Green
        docker-compose up -d
    }
    "docker-down" {
        Write-Host "Stopping Docker services..." -ForegroundColor Green
        docker-compose down
    }
    "docker-logs" {
        Write-Host "Showing Docker logs..." -ForegroundColor Green
        docker-compose logs -f
    }
    "celery-worker" {
        Write-Host "Starting Celery worker..." -ForegroundColor Green
        poetry run celery -A app.core.celery_app worker --loglevel=info
    }
    "celery-beat" {
        Write-Host "Starting Celery beat..." -ForegroundColor Green
        poetry run celery -A app.core.celery_app beat --loglevel=info
    }
    "clean" {
        Write-Host "Cleaning cache files..." -ForegroundColor Green
        Get-ChildItem -Path . -Include __pycache__,*.pyc,*.pyo,.pytest_cache,.mypy_cache -Recurse -Force | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        if (Test-Path "htmlcov") { Remove-Item -Path "htmlcov" -Recurse -Force }
        if (Test-Path "dist") { Remove-Item -Path "dist" -Recurse -Force }
        if (Test-Path "build") { Remove-Item -Path "build" -Recurse -Force }
        Write-Host "Cleaned successfully!" -ForegroundColor Green
    }
    "help" {
        Show-Help
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help
    }
}
