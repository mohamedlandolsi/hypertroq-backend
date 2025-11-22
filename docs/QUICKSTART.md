# Quick Start Guide

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Poetry (optional, but recommended)

## Installation

### 1. Clone and Setup Environment

```bash
cd hypertoq-backend
cp .env.example .env
```

Edit `.env` and update these critical values:
```bash
SECRET_KEY=your-generated-secret-key-here
GOOGLE_API_KEY=your-google-api-key
LEMONSQUEEZY_API_KEY=your-lemonsqueezy-key
```

### 2. Install Dependencies

**Option A: Using Poetry (Recommended)**
```bash
poetry install
poetry shell
```

**Option B: Using pip**
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix/MacOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Start Infrastructure Services

```bash
docker-compose up -d postgres redis
```

Wait for services to be healthy:
```bash
docker-compose ps
```

### 4. Run Database Migrations

```bash
poetry run alembic upgrade head
```

### 5. Start the Application

```bash
poetry run uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing the API

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Save the `access_token` from the response.

### 3. Get Current User

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Development Workflow

### Running Tests

```bash
poetry run pytest
poetry run pytest --cov=app --cov-report=html
```

### Code Formatting

```bash
poetry run black app/
poetry run ruff check app/ --fix
```

### Type Checking

```bash
poetry run mypy app/
```

### Database Migrations

Create a new migration:
```bash
poetry run alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
poetry run alembic upgrade head
```

Rollback migration:
```bash
poetry run alembic downgrade -1
```

### Background Tasks with Celery

Start Celery worker:
```bash
celery -A app.core.celery_app worker --loglevel=info
```

Start Celery beat (scheduler):
```bash
celery -A app.core.celery_app beat --loglevel=info
```

## Docker Compose Usage

Start all services:
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f api
docker-compose logs -f celery_worker
```

Stop all services:
```bash
docker-compose down
```

## Project Structure

```
hypertoq-backend/
├── app/
│   ├── core/              # Configuration and utilities
│   ├── domain/            # Business entities and rules
│   ├── application/       # Use cases and services
│   ├── infrastructure/    # Database, external services
│   ├── presentation/      # API routes and middleware
│   ├── models/            # SQLAlchemy models
│   └── main.py           # Application entry point
├── tests/                 # Test suites
├── alembic/              # Database migrations
├── docker-compose.yml    # Docker services
├── pyproject.toml        # Dependencies
└── README.md             # Documentation
```

## Troubleshooting

### Database Connection Error

1. Check if PostgreSQL is running: `docker-compose ps postgres`
2. Verify DATABASE_URL in `.env`
3. Check logs: `docker-compose logs postgres`

### Redis Connection Error

1. Check if Redis is running: `docker-compose ps redis`
2. Verify REDIS_URL in `.env`
3. Check logs: `docker-compose logs redis`

### Port Already in Use

Change the port in `.env`:
```bash
PORT=8001
```

Or stop the conflicting service.

## Next Steps

1. **Add More Features**: See `ARCHITECTURE.md` for guidance
2. **Configure CI/CD**: Set up GitHub Actions or similar
3. **Deploy**: Use Docker Compose or Kubernetes
4. **Monitor**: Add logging and monitoring tools

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

## Support

For issues or questions:
- Check the documentation at `/docs`
- Review `ARCHITECTURE.md` for design patterns
- Open an issue on GitHub
