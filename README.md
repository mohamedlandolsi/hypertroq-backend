# HypertroQ Backend 🏋️

> A production-ready FastAPI backend for hypertrophy training tracking and program management. Built with Clean Architecture, async operations, and enterprise-grade patterns.

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Features](#features)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

## 🎯 Overview

HypertroQ Backend is a comprehensive API for managing hypertrophy training programs. It helps users track workout volume across 18 muscle groups, create custom exercises, clone program templates, and monitor progress toward muscle growth goals.

**Key Capabilities:**
- 📊 **Volume Tracking**: Calculate weekly training volume per muscle group
- 💪 **18 Muscle Groups**: Complete muscle targeting system
- 🎯 **Smart Programs**: Template-based workout programs with cloning
- ⚡ **Real-time Stats**: Instant volume calculations and recommendations
- 🔐 **Secure Auth**: JWT authentication with email verification
- 💼 **Multi-tenant**: Organization-based resource isolation
- 🎨 **Pro Features**: Subscription tier enforcement (Free/Pro)


## 🛠️ Tech Stack

### Core Framework
- **[FastAPI](https://fastapi.tiangolo.com/)** 0.109+ - Modern async web framework
- **[Python](https://www.python.org/)** 3.13 - Latest Python with performance improvements
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server with hot reload

### Database & Caching
- **[PostgreSQL](https://www.postgresql.org/)** 16 - Primary database with async support
- **[SQLAlchemy](https://www.sqlalchemy.org/)** 2.0 - Modern async ORM
- **[Alembic](https://alembic.sqlalchemy.org/)** - Database migrations
- **[Redis](https://redis.io/)** 7+ - Caching and token storage

### Background Tasks
- **[Celery](https://docs.celeryq.dev/)** 5.3+ - Distributed task queue
- **[Redis](https://redis.io/)** - Celery broker and result backend

### External Integrations
- **[Google Gemini AI](https://ai.google.dev/)** - AI-powered features (future)
- **[LemonSqueezy](https://www.lemonsqueezy.com/)** - Payment processing
- **[Google Cloud Storage](https://cloud.google.com/storage)** - Image/file storage

### Development Tools
- **[Poetry](https://python-poetry.org/)** - Dependency management
- **[Pytest](https://pytest.org/)** - Testing framework
- **[Black](https://black.readthedocs.io/)** - Code formatting
- **[Ruff](https://docs.astral.sh/ruff/)** - Fast Python linter
- **[MyPy](https://mypy.readthedocs.io/)** - Static type checking

### Cloud & Deployment
- **[Docker](https://www.docker.com/)** - Containerization
- **[Google Cloud Run](https://cloud.google.com/run)** - Serverless deployment
- **[Google Cloud SQL](https://cloud.google.com/sql)** - Managed PostgreSQL
- **[Google Cloud Memorystore](https://cloud.google.com/memorystore)** - Managed Redis




## 🏗️ Architecture

This project follows **Clean Architecture** (Uncle Bob) with clear separation of concerns across 4 layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│          (FastAPI routes, middleware, schemas)               │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                         │
│         (Use cases, services, DTOs, business logic)          │
├─────────────────────────────────────────────────────────────┤
│                     Domain Layer                             │
│    (Entities, value objects, interfaces - pure Python)       │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                        │
│   (Database, external APIs, Redis, Celery, Cloud Storage)   │
└─────────────────────────────────────────────────────────────┘
```

### Project Structure

```
hypertroq-backend/
├── app/
│   ├── domain/                      # 🎯 Domain Layer (Pure Business Logic)
│   │   ├── entities/                # Core business entities
│   │   │   ├── user.py             # User entity with roles
│   │   │   ├── exercise.py         # Exercise with muscle contributions
│   │   │   ├── training_program.py # Training program entity
│   │   │   └── organization.py     # Multi-tenant organization
│   │   ├── value_objects/          # Immutable domain objects
│   │   │   ├── equipment.py        # Equipment types enum
│   │   │   ├── muscle_groups.py    # 18 muscle groups enum
│   │   │   └── volume_contribution.py  # Training volume percentages
│   │   └── interfaces/             # Repository contracts
│   │
│   ├── application/                 # 📋 Application Layer (Use Cases)
│   │   ├── services/               # Business logic orchestration
│   │   │   ├── auth_service.py     # Authentication & authorization
│   │   │   ├── user_service.py     # User management
│   │   │   ├── exercise_service.py # Exercise CRUD & filtering
│   │   │   ├── program_service.py  # Program management
│   │   │   └── admin_service.py    # Admin operations
│   │   └── dtos/                   # Data Transfer Objects
│   │       ├── auth_dto.py         # Auth request/response
│   │       ├── user_dto.py         # User data structures
│   │       └── organization_dto.py # Organization DTOs
│   │
│   ├── infrastructure/              # 🔧 Infrastructure Layer (External)
│   │   ├── database/               # Database configuration
│   │   │   ├── connection.py       # Async SQLAlchemy setup
│   │   │   └── base.py            # Base models with mixins
│   │   ├── repositories/           # Data access implementations
│   │   │   ├── user_repository.py
│   │   │   ├── exercise_repository.py
│   │   │   ├── program_repository.py
│   │   │   └── organization_repository.py
│   │   ├── cache/                  # Redis caching
│   │   │   ├── redis_client.py     # Redis connection
│   │   │   ├── token_storage.py    # Token management
│   │   │   └── rate_limiter.py     # API rate limiting
│   │   ├── external/               # Third-party integrations
│   │   │   ├── gemini.py          # Google Gemini AI
│   │   │   └── lemonsqueezy.py    # Payment processing
│   │   └── tasks.py                # Celery background tasks
│   │
│   ├── presentation/                # 🌐 Presentation Layer (HTTP)
│   │   ├── api/                    # API routes
│   │   │   └── v1/                # API version 1
│   │   │       ├── auth.py        # Authentication endpoints
│   │   │       ├── users.py       # User management
│   │   │       ├── exercises.py   # Exercise CRUD
│   │   │       ├── programs.py    # Program management
│   │   │       ├── admin.py       # Admin endpoints
│   │   │       └── health.py      # Health checks
│   │   └── middleware/            # HTTP middleware
│   │       ├── error_handler.py   # Global error handling
│   │       └── logging.py         # Request/response logging
│   │
│   ├── core/                        # ⚙️ Core Configuration
│   │   ├── config.py               # App settings (Pydantic)
│   │   ├── security.py             # JWT, hashing, tokens
│   │   ├── dependencies.py         # FastAPI dependencies
│   │   ├── celery_app.py          # Celery configuration
│   │   └── storage.py             # Cloud Storage setup
│   │
│   ├── models/                      # SQLAlchemy models
│   │   ├── user.py
│   │   ├── exercise.py
│   │   ├── training_program.py
│   │   └── organization.py
│   │
│   └── main.py                      # FastAPI app initialization
│
├── tests/                           # 🧪 Test Suite
│   ├── conftest.py                 # Test fixtures
│   ├── test_auth.py                # Auth endpoint tests
│   ├── test_exercises.py           # Exercise tests (21 tests)
│   ├── test_programs.py            # Program tests (25+ tests)
│   └── test_admin.py               # Admin tests (30+ tests)
│
├── alembic/                         # Database Migrations
│   ├── env.py                      # Alembic configuration
│   └── versions/                   # Migration files
│
├── docs/                            # 📚 Documentation
│   ├── API.md                      # API reference
│   ├── ARCHITECTURE.md             # Architecture guide
│   ├── DATABASE.md                 # Database schema
│   ├── DEPLOYMENT.md               # Deployment guide
│   └── DEVELOPMENT.md              # Development setup
│
├── .env.example                     # Environment template
├── docker-compose.yml              # Local development
├── Dockerfile                       # Production container
├── pyproject.toml                   # Dependencies (Poetry)
├── alembic.ini                      # Alembic config
└── README.md                        # This file
```

### 🔄 Request Flow Example

```
1. HTTP Request → FastAPI Route (presentation/api/v1/exercises.py)
2. Route → Dependency Injection → Service (application/services/exercise_service.py)
3. Service → Repository Interface → Repository Implementation (infrastructure/repositories/)
4. Repository → SQLAlchemy Model → PostgreSQL Database
5. Response flows back through layers with DTOs
```

**Key Principles:**
- ✅ **Dependency Rule**: Inner layers never depend on outer layers
- ✅ **Interfaces**: Domain defines contracts, infrastructure implements
- ✅ **DTOs**: Data crosses boundaries via simple data structures
- ✅ **Testability**: Each layer can be tested independently




## ✨ Features

### Core Functionality
- ✅ **49 REST API Endpoints** - Complete CRUD operations
- ✅ **JWT Authentication** - Access + refresh tokens with email verification
- ✅ **Multi-tenant Architecture** - Organization-based resource isolation
- ✅ **Role-Based Access Control** - User and Admin roles
- ✅ **Subscription Tiers** - Free and Pro with feature enforcement

### Exercise Management
- ✅ **18 Muscle Groups** - Comprehensive muscle targeting system
- ✅ **Volume Contributions** - Fractional muscle engagement (0.25, 0.5, 0.75, 1.0)
- ✅ **Equipment Types** - Barbell, dumbbell, machine, cables, bodyweight
- ✅ **Full-Text Search** - PostgreSQL-powered exercise search
- ✅ **Global + Custom** - Admin templates + user-created exercises

### Program Management
- ✅ **Training Programs** - Complete workout program creation
- ✅ **Split Types** - Upper/Lower, Push/Pull/Legs, Full Body, Custom
- ✅ **Program Templates** - Clone from admin-created templates
- ✅ **Volume Calculations** - Automatic weekly volume per muscle
- ✅ **Smart Recommendations** - Low/Optimal/High/Excessive volume status

### Admin Panel
- ✅ **User Management** - Search, filter, suspend, delete users
- ✅ **Analytics Dashboard** - System statistics and health metrics
- ✅ **Subscription Analytics** - MRR, churn rate, ARPU tracking
- ✅ **Global Resources** - Manage exercises and program templates
- ✅ **Audit Logging** - Track sensitive admin operations

### Technical Features
- ✅ **Async/Await** - Non-blocking I/O throughout
- ✅ **Redis Token Storage** - Password reset (1h) + email verification (24h)
- ✅ **Celery Background Tasks** - Async email sending
- ✅ **Rate Limiting** - API throttling per user/IP
- ✅ **Caching Layer** - Redis caching for global resources
- ✅ **Database Migrations** - Alembic version control
- ✅ **Health Checks** - Database, Redis, system status endpoints
- ✅ **Docker Support** - Full containerization for dev and prod
- ✅ **Comprehensive Testing** - 96+ tests with pytest




## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **PostgreSQL 16+** - [Download](https://www.postgresql.org/download/) or use Docker
- **Redis 7+** - [Download](https://redis.io/download/) or use Docker
- **Docker & Docker Compose** (optional but recommended) - [Download](https://www.docker.com/)
- **Poetry** (optional) - [Install](https://python-poetry.org/docs/#installation)

### Quick Start (Docker - Recommended)

The fastest way to get started is using Docker Compose:

```bash
# 1. Clone the repository
git clone https://github.com/mohamedlandolsi/hypertroq-backend.git
cd hypertroq-backend

# 2. Copy environment file
cp .env.example .env

# 3. Start all services (PostgreSQL, Redis, API)
docker-compose up -d

# 4. Run migrations
docker-compose exec api alembic upgrade head

# 5. (Optional) Seed database with sample data
docker-compose exec api python seed_database.py

# API is now running at http://localhost:8000
# Docs available at http://localhost:8000/docs
```

### Manual Setup (Without Docker)

If you prefer to run services locally:

#### 1. Install Python Dependencies

**Using Poetry (recommended):**
```bash
# Install Poetry if you haven't
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

**Using pip:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Set Up Databases

**Option A: Using Docker for databases only:**
```bash
docker-compose up -d postgres redis
```

**Option B: Local PostgreSQL:**
```bash
# Create databases
psql -U postgres -c "CREATE DATABASE hypertroq;"
psql -U postgres -c "CREATE DATABASE hypertroq_test;"
```

#### 3. Configure Environment

Create `.env` file from the example:

```bash
cp .env.example .env
```

**Edit `.env` with your configuration:**

```ini
# Required Settings
SECRET_KEY=your-super-secret-key-min-32-characters-long!
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/hypertroq
REDIS_URL=redis://localhost:6379/0

# Email Settings (for production)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# API Keys (get from respective services)
GOOGLE_API_KEY=your-google-api-key
LEMONSQUEEZY_API_KEY=your-lemonsqueezy-key

# Frontend URL (for email links)
FRONTEND_URL=http://localhost:3000
```

> ⚠️ **Important**: Change `SECRET_KEY` to a secure random string before deploying!
> Generate one with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

#### 4. Run Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Or with Poetry
poetry run alembic upgrade head
```

#### 5. (Optional) Seed Database

```bash
# Seed with 30 exercises and 3 program templates
python seed_database.py

# Or with Poetry
poetry run python seed_database.py
```

#### 6. Start the API Server

**Development mode (with auto-reload):**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with Poetry
poetry run uvicorn app.main:app --reload
```

**Production mode:**
```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

#### 7. (Optional) Start Celery Workers

```bash
# Terminal 1: Celery worker
celery -A app.core.celery_app worker --loglevel=info

# Terminal 2: Celery beat (for scheduled tasks)
celery -A app.core.celery_app beat --loglevel=info
```

### Verify Installation

Visit these URLs to confirm everything is working:

- **API Health**: http://localhost:8000/api/v1/health
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

You should see a health check response:

```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "0.1.0"
}
```




## 📚 API Documentation

### Interactive Documentation

Once the server is running, access the auto-generated API documentation:

- **Swagger UI** (interactive): http://localhost:8000/docs
- **ReDoc** (clean reference): http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Quick API Overview

**49 REST endpoints across 6 categories:**

#### 🔐 Authentication (`/api/v1/auth`) - 7 endpoints
```bash
POST   /register              # Create new user account
POST   /login                 # Login with email/password
POST   /refresh              # Refresh access token
POST   /password-reset/request  # Request password reset
POST   /password-reset/confirm  # Confirm password reset
POST   /verify-email         # Verify email address
```

#### 👤 User Management (`/api/v1/users`) - 4 endpoints
```bash
GET    /me                   # Get current user profile
PUT    /me                   # Update profile
DELETE /me                   # Delete account
POST   /me/avatar            # Upload profile picture
```

#### 💪 Exercises (`/api/v1/exercises`) - 10 endpoints
```bash
GET    /exercises            # List exercises (filtered, paginated)
GET    /exercises/{id}       # Get exercise details
GET    /exercises/search     # Full-text search
POST   /exercises            # Create custom exercise (Pro)
PUT    /exercises/{id}       # Update exercise
DELETE /exercises/{id}       # Delete exercise
GET    /exercises/muscles/groups      # Get muscle groups
GET    /exercises/equipment/types     # Get equipment types
GET    /exercises/stats/overview      # Get statistics
```

#### 📋 Programs (`/api/v1/programs`) - 10 endpoints
```bash
GET    /programs             # List programs
GET    /programs/{id}        # Get program details
POST   /programs             # Create program (Pro)
POST   /programs/{id}/clone  # Clone template
PUT    /programs/{id}        # Update program
DELETE /programs/{id}        # Delete program
GET    /programs/{id}/stats  # Get volume statistics
POST   /programs/{id}/sessions         # Add workout session
PUT    /programs/{id}/sessions/{sid}   # Update session
DELETE /programs/{id}/sessions/{sid}   # Delete session
```

#### 👑 Admin (`/api/v1/admin`) - 15 endpoints
```bash
# Dashboard & Analytics
GET    /admin/dashboard                # System statistics
GET    /admin/analytics/subscriptions  # Subscription metrics
GET    /admin/analytics/usage          # Usage statistics

# User Management
GET    /admin/users                    # List all users
GET    /admin/users/{id}               # Get user details
PUT    /admin/users/{id}/role          # Update user role
POST   /admin/users/{id}/suspend       # Suspend/unsuspend
DELETE /admin/users/{id}               # Delete user

# Global Resources
GET    /admin/exercises                # Global exercises
POST   /admin/exercises                # Create global exercise
PUT    /admin/exercises/{id}           # Update exercise
DELETE /admin/exercises/{id}           # Delete exercise
GET    /admin/programs                 # Program templates
POST   /admin/programs                 # Create template
PUT    /admin/programs/{id}            # Update template
DELETE /admin/programs/{id}            # Delete template
```

#### 🏥 Health (`/api/v1/health`) - 3 endpoints
```bash
GET    /health               # Basic health check
GET    /health/db            # Database connectivity
GET    /health/redis         # Redis connectivity
```

### Example API Usage

#### Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "full_name": "John Doe"
  }'
```

#### Login and Get Access Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### List Exercises (Authenticated)

```bash
curl -X GET http://localhost:8000/api/v1/exercises \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Create Custom Exercise (Pro Tier)

```bash
curl -X POST http://localhost:8000/api/v1/exercises \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Incline Dumbbell Press",
    "description": "Upper chest focus exercise",
    "equipment": "DUMBBELL",
    "muscle_contributions": {
      "CHEST": 1.0,
      "FRONT_DELTS": 0.5,
      "TRICEPS": 0.5
    }
  }'
```

### Rate Limiting

- **Default**: 60 requests/minute per user
- **Create/Update/Delete**: 10-20 requests/minute
- **Admin endpoints**: 30 requests/minute

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1234567890
```

### Error Responses

All errors follow this structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    },
    "timestamp": "2025-11-23T10:30:00Z",
    "request_id": "abc123"
  }
}
```

Common HTTP status codes:
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (duplicate resource)
- `422` - Unprocessable Entity (validation error)
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error

For detailed API documentation, see [docs/API.md](docs/API.md).




## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_exercises.py

# Run specific test class
pytest tests/test_exercises.py::TestExerciseList

# Run specific test
pytest tests/test_exercises.py::TestExerciseList::test_list_global_exercises

# Run with verbose output
pytest -v

# Run with output (show print statements)
pytest -s
```

### Test Database Setup

Tests use a separate `hypertroq_test` database. Create it:

```bash
# Using provided script
python create_test_db.py

# Or manually
psql -U postgres -c "CREATE DATABASE hypertroq_test;"
```

### Coverage Report

After running tests with coverage, open the HTML report:

```bash
# On Windows
start htmlcov/index.html

# On Unix/MacOS
open htmlcov/index.html
```

**Current Coverage**: 39% (integration tests require database)  
**Target Coverage**: 80%+

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_auth.py             # Authentication (7 tests)
├── test_exercises.py        # Exercises (21 tests)
├── test_programs.py         # Programs (25+ tests)
├── test_admin.py            # Admin (30+ tests)
└── test_user_service.py     # Unit tests
```




## 🚢 Deployment

### Google Cloud Run (Recommended)

1. **Build and push Docker image:**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/hypertroq-backend
```

2. **Deploy to Cloud Run:**
```bash
gcloud run deploy hypertroq-backend \
  --image gcr.io/PROJECT_ID/hypertroq-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL \
  --set-secrets SECRET_KEY=SECRET_KEY:latest
```

3. **Set up Cloud SQL connection:**
```bash
gcloud run services update hypertroq-backend \
  --add-cloudsql-instances PROJECT_ID:REGION:INSTANCE
```

For detailed deployment guide, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

### Environment Variables for Production

```ini
# Security
SECRET_KEY=<64-char-secure-key>
ENVIRONMENT=production
DEBUG=False

# Database (Cloud SQL)
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@/DATABASE?host=/cloudsql/PROJECT:REGION:INSTANCE
DIRECT_URL=<same-as-above>

# Redis (Memorystore)
REDIS_URL=redis://10.0.0.3:6379/0

# Email Service
SMTP_HOST=smtp.sendgrid.net
SMTP_USER=apikey
SMTP_PASSWORD=<sendgrid-api-key>

# API Keys
GOOGLE_API_KEY=<production-key>
LEMONSQUEEZY_API_KEY=<production-key>
LEMONSQUEEZY_WEBHOOK_SECRET=<webhook-secret>

# Frontend
FRONTEND_URL=https://yourdomain.com
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
```

### Pre-Deployment Checklist

- [ ] Change `SECRET_KEY` to secure random value
- [ ] Set `DEBUG=False`
- [ ] Configure production database (Cloud SQL)
- [ ] Set up Redis (Memorystore)
- [ ] Configure email service (SendGrid/Resend)
- [ ] Add all API keys to Secret Manager
- [ ] Run database migrations
- [ ] Seed database with initial data
- [ ] Configure CORS for production domain
- [ ] Set up monitoring (Sentry, Cloud Monitoring)
- [ ] Configure backups (Cloud SQL auto-backup)
- [ ] Set up CI/CD (GitHub Actions)




## 🔧 Development Commands

### Basic Commands

```bash
# Start development server (auto-reload)
poetry run uvicorn app.main:app --reload

# Or using the PowerShell script
.\commands.ps1 dev

# Format code with Black
poetry run black app/
# Or
.\commands.ps1 format

# Lint code with Ruff
poetry run ruff check app/

# Type checking with MyPy
poetry run mypy app/
```

### Database Migrations

```bash
# Create new migration after modifying models
poetry run alembic revision --autogenerate -m "add products table"

# Apply all pending migrations
poetry run alembic upgrade head
# Or
.\commands.ps1 migrate

# Rollback last migration
poetry run alembic downgrade -1

# View migration history
poetry run alembic history

# Check current migration version
poetry run alembic current
```

### Celery Background Tasks

```bash
# Start Celery worker
poetry run celery -A app.core.celery_app worker --loglevel=info
# Or
.\commands.ps1 celery-worker

# Start Celery beat (scheduled tasks)
poetry run celery -A app.core.celery_app beat --loglevel=info
# Or
.\commands.ps1 celery-beat

# Monitor Celery tasks (Flower)
poetry run celery -A app.core.celery_app flower
```




## 🐳 Docker Commands

```bash
# Start all services (PostgreSQL, Redis, API)
docker-compose up -d

# View logs for all services
docker-compose logs -f

# View API logs only
docker-compose logs -f api

# View database logs
docker-compose logs -f postgres

# Rebuild containers after code changes
docker-compose up -d --build

# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ clears database)
docker-compose down -v

# Access PostgreSQL shell
docker-compose exec postgres psql -U hypertoq -d hypertoq

# Access Redis CLI
docker-compose exec redis redis-cli

# Execute command in API container
docker-compose exec api poetry run alembic upgrade head
```




## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Code Style

- Follow **PEP 8** Python style guide
- Use **type hints** for all function parameters and return values
- Write **docstrings** for all classes and public methods
- Run Black formatter before committing: `poetry run black app/`
- Run Ruff linter: `poetry run ruff check app/`
- Use meaningful variable and function names

### Clean Architecture Principles

1. **Domain layer** contains pure business logic (no framework dependencies)
2. **Application layer** orchestrates use cases (services, DTOs)
3. **Infrastructure layer** handles external dependencies (database, APIs)
4. **Presentation layer** manages HTTP interface (routes, middleware)
5. Always use **dependency injection** (see `app/core/dependencies.py`)
6. Entities → DTOs conversion happens in services
7. **Never import outer layers from inner layers**

### Testing Requirements

- Write **unit tests** for all services and repositories
- Write **integration tests** for API endpoints
- Aim for **80%+ code coverage**
- Test both success and error scenarios
- Use fixtures from `tests/conftest.py`
- Mock external dependencies (Redis, Gemini API, LemonSqueezy)

### Pull Request Process

1. **Create a feature branch**: `git checkout -b feature/your-feature-name`
2. **Write tests** for your changes
3. **Ensure all tests pass**: `poetry run pytest`
4. **Run formatters and linters**
5. **Update documentation** if needed
6. **Submit PR** with clear description
7. **Wait for code review** and address feedback

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Example**:
```
feat(programs): add program cloning endpoint

- Add POST /programs/{id}/clone endpoint
- Implement clone_program service method
- Add tests for program cloning
- Update API documentation

Closes #123
```




## 🐛 Troubleshooting

### Database Connection Issues

**Problem**: `could not connect to server: Connection refused`

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Verify connection string in .env
cat .env | grep DATABASE_URL
```

**Problem**: `relation "users" does not exist`

```bash
# Run migrations to create tables
poetry run alembic upgrade head

# Check current migration version
poetry run alembic current

# If migrations fail, verify database exists
docker-compose exec postgres psql -U hypertoq -l
```

### Redis Connection Issues

**Problem**: `Error connecting to Redis: Connection refused`

```bash
# Check if Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Restart Redis
docker-compose restart redis

# Check Redis logs
docker-compose logs redis
```

### Celery Task Issues

**Problem**: Background tasks not executing

```bash
# Check if Celery worker is running
poetry run celery -A app.core.celery_app inspect active

# Start Celery worker if not running
.\commands.ps1 celery-worker

# Check Celery logs for errors
# Tasks should appear in worker output

# Check Redis (Celery uses it as broker)
docker-compose exec redis redis-cli
> KEYS celery*
> LLEN celery
```

### Migration Issues

**Problem**: `Target database is not up to date`

```bash
# Check current migration status
poetry run alembic current

# View migration history
poetry run alembic history --verbose

# Upgrade to latest migration
poetry run alembic upgrade head

# If you need to reset (⚠️ WARNING: destroys all data!)
poetry run alembic downgrade base
poetry run alembic upgrade head
```

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app'`

```bash
# Ensure virtual environment is activated
poetry shell

# Reinstall all dependencies
poetry install

# Check Python path includes current directory
python -c "import sys; print(sys.path)"

# Verify you're in the project root
pwd
# Should show: .../hypertroq-backend
```

**Problem**: Circular import errors

- Review dependency graph - inner layers should **never** import from outer layers
- Check import order in `__init__.py` files
- Use dependency injection instead of direct imports
- Move shared types to `domain/interfaces/` or `domain/value_objects/`

### Test Failures

**Problem**: Tests fail with database errors

```bash
# Create test database
python create_test_db.py

# Run migrations on test database
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5433/hypertroq_test"
poetry run alembic upgrade head

# Run specific test with verbose output
poetry run pytest tests/test_user_service.py::test_create_user -vv --tb=short
```

**Problem**: Tests hang or timeout

- Check if Docker containers are running: `docker-compose ps`
- Ensure Redis is accessible: `docker-compose exec redis redis-cli ping`
- Verify test database connection string in `tests/conftest.py`

### Port Already in Use

**Problem**: `OSError: [WinError 10048] Only one usage of each socket address`

```powershell
# Windows: Find process using port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object -Property OwningProcess

# Kill the process
Stop-Process -Id <PROCESS_ID> -Force

# Or use a different port
poetry run uvicorn app.main:app --port 8001
```

### Environment Variables Not Loading

**Problem**: App can't find required environment variables

```bash
# Verify .env file exists in project root
ls .env

# Check if python-dotenv is installed
poetry show python-dotenv

# Manually test loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('DATABASE_URL'))"

# PowerShell: Manually set environment variable for testing
$env:DATABASE_URL="postgresql+asyncpg://..."
```




## 📚 Additional Documentation

For more detailed information, check out these documentation files:

- **[API.md](docs/API.md)** - Comprehensive API endpoint documentation with examples
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Deep dive into clean architecture patterns
- **[DATABASE.md](docs/DATABASE.md)** - Database schema, relationships, and design decisions
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guide for Google Cloud
- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Local development setup and workflow

*(Note: These documentation files will be created in the next step)*




## 🌐 Environment Variables Reference

Key environment variables (see `.env.example` for full list):

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection (async driver) | ✅ | - |
| `DIRECT_URL` | PostgreSQL direct connection (for migrations) | ✅ | - |
| `REDIS_URL` | Redis connection string | ✅ | - |
| `SECRET_KEY` | JWT signing key (min 32 chars) | ✅ | - |
| `ENVIRONMENT` | Environment name (`development`/`production`) | ❌ | `development` |
| `DEBUG` | Enable debug mode | ❌ | `True` |
| `BACKEND_CORS_ORIGINS` | CORS allowed origins (JSON array) | ✅ | `[]` |
| `FRONTEND_URL` | Frontend URL for email links | ✅ | - |
| `GOOGLE_API_KEY` | Google Gemini AI API key | ✅ | - |
| `GEMINI_MODEL` | Gemini model name | ❌ | `gemini-2.0-flash` |
| `LEMONSQUEEZY_API_KEY` | Payment processing API key | ✅ | - |
| `LEMONSQUEEZY_STORE_ID` | LemonSqueezy store ID | ✅ | - |
| `LEMONSQUEEZY_WEBHOOK_SECRET` | Webhook signature verification | ✅ | - |
| `SMTP_HOST` | Email server hostname | ❌ | - |
| `SMTP_PORT` | Email server port | ❌ | `587` |
| `SMTP_USER` | Email authentication username | ❌ | - |
| `SMTP_PASSWORD` | Email authentication password | ❌ | - |
| `CELERY_BROKER_URL` | Celery broker URL | ❌ | Uses `REDIS_URL` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token lifetime | ❌ | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT refresh token lifetime | ❌ | `7` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | ❌ | - |
| `GOOGLE_CLOUD_STORAGE_BUCKET` | Cloud Storage bucket name | ❌ | - |




## 📝 License

MIT License - feel free to use this project for learning or production.

See [LICENSE](LICENSE) file for details.




## 🆘 Support

For issues and questions:

- 📖 **Documentation**: Check the [Interactive API Docs](http://localhost:8000/docs)
- 📚 **Guides**: Review the [docs folder](docs/) for detailed guides
- 🐛 **Bug Reports**: Open an issue on [GitHub Issues](https://github.com/yourusername/hypertroq-backend/issues)
- 💬 **Discussions**: Start a conversation on [GitHub Discussions](https://github.com/yourusername/hypertroq-backend/discussions)
- 📧 **Email**: Contact the maintainers at support@hypertroq.com




## 🙏 Acknowledgments

Built with these amazing open-source projects:

- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework for building APIs
- [SQLAlchemy](https://www.sqlalchemy.org/) - The Python SQL toolkit and ORM
- [Pydantic](https://docs.pydantic.dev/) - Data validation using Python type hints
- [Alembic](https://alembic.sqlalchemy.org/) - Lightweight database migration tool
- [Celery](https://docs.celeryq.dev/) - Distributed task queue
- [Redis](https://redis.io/) - In-memory data structure store
- [PostgreSQL](https://www.postgresql.org/) - The world's most advanced open source database

Special thanks to the open-source community for making projects like this possible! 🚀

---

**Built with ❤️ using FastAPI and Clean Architecture**


