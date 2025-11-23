# Development Guide

Complete guide for developing HypertroQ Backend locally.

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Strategy](#testing-strategy)
- [Database Management](#database-management)
- [Background Tasks](#background-tasks)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Python 3.11+ (3.13 recommended)
- Poetry 1.7+
- Docker & Docker Compose
- PostgreSQL 16+ (or use Docker)
- Redis 7+ (or use Docker)
- Git

### Initial Setup

1. **Clone repository:**
```bash
git clone https://github.com/yourusername/hypertroq-backend.git
cd hypertroq-backend
```

2. **Install dependencies:**
```bash
# With Poetry (recommended)
poetry install

# Or with pip
pip install -r requirements.txt
```

3. **Start infrastructure:**
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Verify services are running
docker-compose ps
```

4. **Configure environment:**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Important: Generate a secure SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

5. **Run migrations:**
```bash
poetry run alembic upgrade head
```

6. **Seed database (optional):**
```bash
poetry run python seed_database.py
```

7. **Start development server:**
```bash
# Auto-reload on code changes
poetry run uvicorn app.main:app --reload

# Or use PowerShell command
.\commands.ps1 dev
```

### Verify Setup

Visit these URLs:
- http://localhost:8000/api/v1/health - Health check
- http://localhost:8000/docs - Interactive API docs
- http://localhost:8000/redoc - ReDoc documentation

---

## Project Structure

```
hypertroq-backend/
├── app/                          # Main application code
│   ├── domain/                   # Business logic layer (innermost)
│   │   ├── entities/             # Business entities (User, Exercise, Program)
│   │   ├── interfaces/           # Repository and service interfaces
│   │   └── value_objects/        # Immutable domain objects
│   ├── application/              # Application logic layer
│   │   ├── services/             # Business use cases and orchestration
│   │   └── dtos/                 # Data transfer objects
│   ├── infrastructure/           # External concerns layer
│   │   ├── database/             # Database connection, models, migrations
│   │   ├── repositories/         # Repository implementations
│   │   ├── external/             # Third-party API integrations
│   │   └── cache/                # Redis caching
│   ├── presentation/             # HTTP interface layer (outermost)
│   │   ├── api/                  # API routes and endpoints
│   │   └── middleware/           # HTTP middleware
│   ├── core/                     # Cross-cutting concerns
│   │   ├── config.py             # Settings and configuration
│   │   ├── dependencies.py       # Dependency injection
│   │   ├── security.py           # Authentication and JWT
│   │   └── celery_app.py         # Background task configuration
│   └── main.py                   # FastAPI application entry point
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration files
│   └── env.py                    # Alembic configuration
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests (services, repositories)
│   ├── integration/              # API endpoint tests
│   └── conftest.py               # Shared fixtures
├── docs/                         # Documentation
├── docker-compose.yml            # Docker services configuration
├── Dockerfile                    # Production Docker image
├── pyproject.toml                # Poetry dependencies
└── .env                          # Environment variables (not committed)
```

### Layer Responsibilities

#### Domain Layer (Core Business Logic)
- **Entities**: Objects with identity (User, Exercise, Program)
- **Value Objects**: Immutable objects (Email, MuscleContribution)
- **Interfaces**: Abstract contracts for repositories and services
- **Rules**: Pure business logic, no framework dependencies

#### Application Layer (Use Cases)
- **Services**: Orchestrate business operations
- **DTOs**: Define data structures for communication
- **Validation**: Business rule validation
- **Error Handling**: Application-specific exceptions

#### Infrastructure Layer (External Concerns)
- **Repositories**: Database access implementations
- **External Services**: Gemini AI, LemonSqueezy, Cloud Storage
- **Cache**: Redis integration
- **Database Models**: SQLAlchemy models

#### Presentation Layer (HTTP Interface)
- **API Routes**: FastAPI endpoints
- **Schemas**: Pydantic request/response models
- **Middleware**: Auth, CORS, rate limiting, error handling
- **Dependency Injection**: FastAPI dependencies

---

## Development Workflow

### Daily Workflow

1. **Pull latest changes:**
```bash
git pull origin main
```

2. **Update dependencies:**
```bash
poetry install
```

3. **Apply new migrations:**
```bash
poetry run alembic upgrade head
```

4. **Start development server:**
```bash
poetry run uvicorn app.main:app --reload
```

5. **Make changes** and test in browser at http://localhost:8000/docs

6. **Run tests:**
```bash
poetry run pytest
```

7. **Format and lint:**
```bash
poetry run black app/
poetry run ruff check app/
```

8. **Commit changes:**
```bash
git add .
git commit -m "feat(scope): description"
git push origin feature-branch
```

### Feature Development

1. **Create feature branch:**
```bash
git checkout -b feature/your-feature-name
```

2. **Implement feature** following clean architecture:
   - Add entity/value object in `domain/`
   - Define interface in `domain/interfaces/`
   - Create service in `application/services/`
   - Implement repository in `infrastructure/repositories/`
   - Add route in `presentation/api/`

3. **Write tests:**
   - Unit tests for services
   - Integration tests for API endpoints

4. **Update documentation:**
   - Add docstrings
   - Update API.md if adding endpoints
   - Update README.md if needed

5. **Create pull request** with description

---

## Coding Standards

### Python Style Guide

Follow **PEP 8** with these additions:

```python
# Use type hints everywhere
def get_user(user_id: UUID) -> UserEntity:
    pass

# Use descriptive variable names
# BAD
u = get_user(id)

# GOOD
user = get_user(user_id)

# Use docstrings for all public functions
def calculate_volume(exercises: list[Exercise]) -> dict[str, float]:
    """
    Calculate total training volume per muscle group.
    
    Args:
        exercises: List of exercises with sets and muscle contributions
        
    Returns:
        Dictionary mapping muscle groups to total volume (sets)
        
    Example:
        >>> exercises = [Exercise(name="Bench", sets=4, ...)]
        >>> calculate_volume(exercises)
        {"CHEST": 4.0, "TRICEPS": 2.0}
    """
    pass

# Use early returns for error cases
def process_payment(user: User, amount: float):
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    # Main logic here
    pass
```

### Clean Architecture Rules

1. **Dependency Direction**: Inner layers never depend on outer layers
```python
# BAD - Domain importing from infrastructure
from app.infrastructure.database.models import UserModel  # ❌

# GOOD - Infrastructure importing from domain
from app.domain.entities.user import UserEntity  # ✅
```

2. **Use Interfaces**:
```python
# domain/interfaces/user_repository.py
class IUserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        ...

# application/services/user_service.py
class UserService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
```

3. **DTOs for Layer Communication**:
```python
# application/dtos/user_dto.py
class UserResponseDTO(BaseModel):
    id: UUID
    email: str
    full_name: str

# service returns DTO, not entity
async def get_user(user_id: UUID) -> UserResponseDTO:
    entity = await self.repo.get_by_id(user_id)
    return UserResponseDTO.from_entity(entity)
```

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_CASE`
- **Private attributes**: `_leading_underscore`
- **DTOs**: `*DTO` or `*Schema`
- **Entities**: `*Entity`
- **Repositories**: `*Repository`
- **Services**: `*Service`

### Import Order

```python
# 1. Standard library
import os
from datetime import datetime

# 2. Third-party
from fastapi import APIRouter
from sqlalchemy import select

# 3. Local application
from app.domain.entities.user import UserEntity
from app.application.dtos.user_dto import UserResponseDTO
```

---

## Testing Strategy

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Pure business logic tests
│   ├── test_services.py
│   └── test_repositories.py
├── integration/             # API endpoint tests
│   ├── test_auth_api.py
│   ├── test_exercises_api.py
│   └── test_programs_api.py
└── e2e/                     # End-to-end scenarios (future)
```

### Writing Tests

#### Unit Tests (Services)

```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import Mock
from app.application.services.user_service import UserService

@pytest.fixture
def mock_user_repository():
    return Mock()

@pytest.fixture
def user_service(mock_user_repository):
    return UserService(mock_user_repository)

async def test_create_user_success(user_service, mock_user_repository):
    # Arrange
    mock_user_repository.get_by_email.return_value = None
    mock_user_repository.create.return_value = UserEntity(...)
    
    # Act
    result = await user_service.create_user(
        email="test@example.com",
        password="SecurePass123!",
        full_name="Test User"
    )
    
    # Assert
    assert result.email == "test@example.com"
    mock_user_repository.create.assert_called_once()

async def test_create_user_duplicate_email(user_service, mock_user_repository):
    # Arrange
    mock_user_repository.get_by_email.return_value = UserEntity(...)
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await user_service.create_user(
            email="existing@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )
    
    assert exc.value.status_code == 409
```

#### Integration Tests (API)

```python
# tests/integration/test_auth_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user_success():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "New User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@example.com"

def test_register_duplicate_email():
    # First registration
    client.post("/api/v1/auth/register", json={...})
    
    # Second registration with same email
    response = client.post("/api/v1/auth/register", json={...})
    
    assert response.status_code == 409
    assert "already registered" in response.json()["error"]["message"]
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_user_service.py

# Run specific test
poetry run pytest tests/unit/test_user_service.py::test_create_user_success

# Run with verbose output
poetry run pytest -vv

# Run only integration tests
poetry run pytest tests/integration/

# Run tests matching pattern
poetry run pytest -k "test_create"
```

### Test Coverage

Target **80%+ coverage** for business logic:

```bash
# Generate coverage report
poetry run pytest --cov=app --cov-report=html

# View report
# Open htmlcov/index.html in browser
```

Focus coverage on:
- ✅ Services (business logic)
- ✅ Repositories (data access)
- ✅ API endpoints (integration)
- ⚠️ Less critical: Models, DTOs, config

---

## Database Management

### Creating Migrations

```bash
# After modifying models in infrastructure/database/models/
poetry run alembic revision --autogenerate -m "add user_preferences table"

# Review generated migration in alembic/versions/
# Edit if needed (alembic can't detect everything)

# Apply migration
poetry run alembic upgrade head
```

### Migration Best Practices

1. **Review auto-generated migrations** - Alembic misses some changes
2. **Use descriptive names** - `add_user_preferences` not `update_1`
3. **Test both upgrade and downgrade**
4. **Never edit applied migrations** - Create new one instead
5. **Backup production data** before migration

### Common Migration Scenarios

#### Add Column

```python
def upgrade():
    op.add_column(
        'users',
        sa.Column('bio', sa.String(500), nullable=True)
    )

def downgrade():
    op.drop_column('users', 'bio')
```

#### Add Index

```python
def upgrade():
    op.create_index(
        'ix_exercises_name',
        'exercises',
        ['name'],
        unique=False
    )

def downgrade():
    op.drop_index('ix_exercises_name', table_name='exercises')
```

#### Data Migration

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add column
    op.add_column('users', sa.Column('full_name', sa.String(255)))
    
    # Migrate data
    connection = op.get_bind()
    connection.execute("""
        UPDATE users 
        SET full_name = CONCAT(first_name, ' ', last_name)
    """)
    
    # Make column non-nullable
    op.alter_column('users', 'full_name', nullable=False)
```

### Database Utilities

```bash
# Check current migration
poetry run alembic current

# View migration history
poetry run alembic history

# Downgrade one migration
poetry run alembic downgrade -1

# Downgrade to specific version
poetry run alembic downgrade <revision_id>

# Reset database (⚠️ destroys data!)
poetry run alembic downgrade base
poetry run alembic upgrade head
```

---

## Background Tasks

### Celery Architecture

```
FastAPI App → Redis (Broker) → Celery Worker → Task Execution
                    ↓
              Result Backend (Redis)
```

### Creating Tasks

```python
# app/infrastructure/tasks.py
from app.core.celery_app import celery_app

@celery_app.task(name="send_welcome_email")
def send_welcome_email(user_id: str, email: str):
    """Send welcome email to new user."""
    # Implementation
    return {"status": "sent", "email": email}

@celery_app.task(name="generate_embeddings", bind=True, max_retries=3)
def generate_embeddings(self, exercise_id: str):
    """Generate embeddings for exercise using Gemini."""
    try:
        # Implementation
        pass
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### Calling Tasks

```python
# In your service
from app.infrastructure.tasks import send_welcome_email

class UserService:
    async def create_user(self, ...):
        # Create user
        user = await self.repo.create(...)
        
        # Trigger background task
        send_welcome_email.delay(str(user.id), user.email)
        
        return user
```

### Running Celery

```bash
# Terminal 1: Start worker
poetry run celery -A app.core.celery_app worker --loglevel=info

# Terminal 2: Start beat (scheduled tasks)
poetry run celery -A app.core.celery_app beat --loglevel=info

# Or use PowerShell scripts
.\commands.ps1 celery-worker
.\commands.ps1 celery-beat
```

### Monitoring Celery

```bash
# View active tasks
poetry run celery -A app.core.celery_app inspect active

# View registered tasks
poetry run celery -A app.core.celery_app inspect registered

# Start Flower (web UI)
poetry run celery -A app.core.celery_app flower
# Open http://localhost:5555
```

---

## Debugging

### VS Code Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload"
      ],
      "jinja": true,
      "justMyCode": false
    },
    {
      "name": "Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "-vv"
      ]
    }
  ]
}
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# In your code
logger.debug("Detailed debug information")
logger.info("User registered", extra={"user_id": user.id})
logger.warning("API rate limit approaching")
logger.error("Failed to process payment", exc_info=True)
```

### Database Query Debugging

```python
# Enable SQL echo in development
# app/infrastructure/database/connection.py
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Print all SQL queries
    pool_size=10
)
```

### API Request Debugging

```python
# Add to middleware for detailed request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    logger.debug(f"Headers: {request.headers}")
    
    response = await call_next(request)
    
    logger.info(f"Response: {response.status_code}")
    return response
```

---

## Common Tasks

### Add New Endpoint

1. **Define route** in `presentation/api/v1/`:
```python
# presentation/api/v1/exercises.py
@router.post("/exercises/{exercise_id}/favorite")
async def favorite_exercise(
    exercise_id: UUID,
    current_user_id: CurrentUserDep,
    service: ExerciseServiceDep
):
    return await service.favorite_exercise(exercise_id, current_user_id)
```

2. **Add service method** in `application/services/`:
```python
# application/services/exercise_service.py
async def favorite_exercise(
    self, 
    exercise_id: UUID, 
    user_id: UUID
) -> ExerciseResponseDTO:
    # Implementation
    pass
```

3. **Update repository** if needed in `infrastructure/repositories/`

4. **Write tests** in `tests/integration/`

### Add New Entity

1. **Create entity** in `domain/entities/`:
```python
# domain/entities/workout.py
class WorkoutEntity(Entity):
    def __init__(self, ...):
        # Constructor
        pass
```

2. **Create SQLAlchemy model** in `infrastructure/database/models/`:
```python
# infrastructure/database/models/workout.py
class WorkoutModel(BaseModel):
    __tablename__ = "workouts"
    # Fields
```

3. **Create migration**:
```bash
poetry run alembic revision --autogenerate -m "add workouts table"
```

4. **Create repository** in `infrastructure/repositories/`

5. **Create service** in `application/services/`

6. **Add API routes** in `presentation/api/v1/`

### Add External API Integration

1. **Create client** in `infrastructure/external/`:
```python
# infrastructure/external/sendgrid_client.py
class SendGridClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def send_email(self, to: str, subject: str, body: str):
        # Implementation
        pass
```

2. **Add configuration** in `core/config.py`:
```python
class Settings(BaseSettings):
    SENDGRID_API_KEY: str
```

3. **Use in services** via dependency injection

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
```bash
# Ensure you're in project root
pwd

# Activate virtual environment
poetry shell

# Reinstall dependencies
poetry install
```

#### 2. Database Connection Failed

**Problem**: `could not connect to server`

**Solution**:
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres

# Check DATABASE_URL in .env
```

#### 3. Alembic Can't Find Models

**Problem**: `Target database is not up to date`

**Solution**:
```bash
# Ensure all models are imported in models/__init__.py
# Run migrations
poetry run alembic upgrade head
```

#### 4. Tests Fail with "Database does not exist"

**Solution**:
```bash
# Create test database
python create_test_db.py

# Or manually
docker-compose exec postgres psql -U postgres
CREATE DATABASE hypertroq_test;
```

#### 5. Port Already in Use

**Solution**:
```powershell
# Windows PowerShell
Get-NetTCPConnection -LocalPort 8000 | 
  Select-Object -ExpandProperty OwningProcess | 
  ForEach-Object { Stop-Process -Id $_ -Force }
```

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

**Happy coding! 🚀**
