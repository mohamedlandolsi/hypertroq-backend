# HyperToQ Backend

A modern FastAPI backend application built with clean architecture principles, featuring async operations, background tasks, AI integration, and payment processing.

## 🏗️ Architecture

This project follows **Clean Architecture** principles with clear separation of concerns:

```
hypertoq-backend/
├── app/
│   ├── domain/              # Enterprise Business Rules
│   │   ├── entities/        # Domain entities
│   │   ├── value_objects/   # Value objects
│   │   └── interfaces/      # Repository & service interfaces
│   ├── application/         # Application Business Rules
│   │   ├── use_cases/       # Use case implementations
│   │   ├── services/        # Application services
│   │   └── dtos/           # Data Transfer Objects
│   ├── infrastructure/      # Frameworks & Drivers
│   │   ├── database/        # Database setup & migrations
│   │   ├── repositories/    # Repository implementations
│   │   ├── external/        # External service integrations
│   │   └── cache/          # Caching implementations
│   ├── presentation/        # Interface Adapters
│   │   ├── api/            # API routes & controllers
│   │   ├── schemas/        # Request/Response schemas
│   │   └── middleware/     # HTTP middleware
│   └── core/               # Core configurations
│       ├── config.py       # Application settings
│       ├── security.py     # Security utilities
│       └── dependencies.py # Dependency injection
├── tests/                  # Test suites
├── alembic/               # Database migrations
├── docker-compose.yml     # Local development setup
└── pyproject.toml         # Project dependencies
```

## 🚀 Features

- ✅ **FastAPI** with async/await support
- ✅ **Clean Architecture** with proper layer separation
- ✅ **SQLAlchemy 2.0** with async PostgreSQL
- ✅ **Alembic** for database migrations
- ✅ **JWT Authentication** with refresh tokens
- ✅ **Redis** for caching and sessions
- ✅ **Celery** for background tasks
- ✅ **Google Gemini AI** integration
- ✅ **LemonSqueezy** payment processing
- ✅ **Docker & Docker Compose** for local development
- ✅ **Poetry** for dependency management
- ✅ **Comprehensive testing** with pytest
- ✅ **Code quality** with Black, Ruff, and MyPy

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Poetry (optional, can use pip)

## 🛠️ Setup

### 1. Clone and Navigate

```bash
cd hypertoq-backend
```

### 2. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your configuration values, especially:
- `SECRET_KEY` - Generate a secure secret key
- `GOOGLE_API_KEY` - Your Google AI API key
- `LEMONSQUEEZY_API_KEY` - Your LemonSqueezy API key

### 3. Install Dependencies

**Using Poetry (recommended):**
```bash
poetry install
```

**Using pip:**
```bash
pip install -r requirements.txt
```

### 4. Start Infrastructure Services

```bash
docker-compose up -d postgres redis
```

### 5. Run Database Migrations

```bash
# Using Poetry
poetry run alembic upgrade head

# Or directly
alembic upgrade head
```

### 6. Start the Application

**Development mode:**
```bash
# Using Poetry
poetry run uvicorn app.main:app --reload

# Or with Docker
docker-compose up api
```

**Production mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7. Start Celery Workers (Optional)

```bash
# Worker
celery -A app.core.celery_app worker --loglevel=info

# Beat scheduler
celery -A app.core.celery_app beat --loglevel=info

# Or with Docker
docker-compose up celery_worker celery_beat
```

## 📚 API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_users.py
```

## 🔧 Development Commands

```bash
# Format code
poetry run black app/

# Lint code
poetry run ruff check app/

# Type checking
poetry run mypy app/

# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Rebuild containers
docker-compose up -d --build

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## 📁 Project Structure Details

### Domain Layer
- **Entities**: Core business objects with identity (User, Product, Order)
- **Value Objects**: Immutable objects without identity (Email, Money, Address)
- **Interfaces**: Contracts for repositories and services

### Application Layer
- **Use Cases**: Application-specific business rules
- **Services**: Coordinate use cases and domain logic
- **DTOs**: Data structures for inter-layer communication

### Infrastructure Layer
- **Repositories**: Database access implementations
- **External Services**: Third-party API integrations
- **Database**: Connection, session management, migrations

### Presentation Layer
- **API Routes**: HTTP endpoints and controllers
- **Schemas**: Request/response validation (Pydantic)
- **Middleware**: Authentication, logging, error handling

## 🔒 Security

- JWT-based authentication with access and refresh tokens
- Password hashing with bcrypt
- CORS configuration
- Rate limiting (middleware)
- SQL injection protection (SQLAlchemy ORM)
- Input validation (Pydantic)

## 🌐 Environment Variables

Key environment variables (see `.env.example` for full list):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `SECRET_KEY` | JWT secret key | - |
| `GOOGLE_API_KEY` | Google AI API key | - |
| `LEMONSQUEEZY_API_KEY` | Payment API key | - |

## 🤝 Contributing

1. Follow the clean architecture principles
2. Write tests for new features
3. Run linters before committing
4. Update documentation as needed

## 📝 License

MIT License - feel free to use this project for learning or production.

## 🆘 Support

For issues and questions:
- Check the [API documentation](http://localhost:8000/docs)
- Review the code examples in the repository
- Open an issue on GitHub

---

**Built with ❤️ using FastAPI and Clean Architecture**
