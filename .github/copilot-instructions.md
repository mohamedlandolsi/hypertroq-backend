# HypertroQ Backend - AI Agent Instructions

## Business Domain: Hypertrophy Training SaaS

**Core Concepts**:
- **Hypertrophy**: Muscle growth through progressive overload
- **Volume Tracking**: Total sets per muscle group/week (key metric for growth)
- **18 Muscle Groups**: Chest, Lats, Traps/Rhomboids, Front/Side/Rear Delts, Triceps, Elbow Flexors, Forearms, Spinal Erectors, Abs, Obliques, Glutes, Quads, Hamstrings, Adductors, Calves
- **Volume Contribution**: Each exercise contributes fractionally (0.25, 0.5, 0.75, 1.0) to muscles

**Domain Hierarchy**:
```
Program → Sessions (Workouts) → Exercises → Sets
```

**Structure Types**:
- **Weekly**: User selects specific days (Mon/Wed/Fri for 3-day split)
- **Cyclic**: Days on/off pattern (3 days on, 1 day off)

**Critical Business Rules**:
- Minimum 10 sets/muscle/week for hypertrophy
- Maximum 20-25 sets/muscle/week (recovery limit)
- Volume = Sum(exercise_sets × muscle_contribution)
- Pro tier required for custom exercises and program creation
- Free tier: 10 AI queries/month, Pro: unlimited

## Architecture Overview
**Clean Architecture with 4-layer separation** (see `ARCHITECTURE.md`):
- **Domain Layer** (`app/domain/`): Pure business logic - entities, value objects, interfaces (no framework dependencies)
- **Application Layer** (`app/application/`): Use cases, services, DTOs (orchestration)
- **Infrastructure Layer** (`app/infrastructure/`): Database, external APIs (Gemini AI, LemonSqueezy), Redis, Celery
- **Presentation Layer** (`app/presentation/`): FastAPI routes, middleware

**Dependency Rule**: Inner layers never depend on outer layers. Use interfaces/protocols for inversion.

## Critical Database Configuration

### Google Cloud SQL + pgBouncer Compatibility
- **Use `DIRECT_URL`** for Alembic migrations (bypasses pgBouncer)
- **Use `DATABASE_URL`** for application runtime (pooled connection)
- **pgBouncer detection**: Automatically sets `statement_cache_size=0` when "pooler" or "pgbouncer" in URL
- **Cloud SQL Unix Socket**: For production, use Unix socket connection: `postgresql+asyncpg://USER:PASSWORD@/DATABASE?host=/cloudsql/PROJECT:REGION:INSTANCE`
- See `app/infrastructure/database/connection.py` DatabaseManager class

### Database Session Pattern
```python
# In routes - use FastAPI dependency
from app.core.dependencies import DatabaseDep
@router.get("/endpoint")
async def handler(db: DatabaseDep):
    # Session auto-commits on success, rolls back on exception
```

## Essential Patterns

### 1. Repository Pattern (Data Access)
**Implementation**: See `app/infrastructure/repositories/user_repository.py`
- Repository takes `AsyncSession` in constructor
- Converts between Entity (domain) ↔ Model (SQLAlchemy)
- Methods: `get_by_id()`, `get_by_email()`, `create()`, `update()`, `delete()`

### 2. Service Layer (Business Logic)
**Implementation**: See `app/application/services/user_service.py`
- Service takes Repository interface in constructor
- Raises `HTTPException` with proper status codes
- Returns DTOs, not entities
- Example: `create_user()` checks existence, hashes password, creates entity

### 3. Dependency Injection in Routes
**Pattern**: See `app/presentation/api/v1/users.py`
```python
def get_user_service(db: DatabaseDep) -> UserService:
    return UserService(UserRepository(db))

@router.get("/me")
async def get_current_user(
    current_user_id: CurrentUserDep,  # JWT auth
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    return await user_service.get_user(UUID(current_user_id))
```

### 4. Entity Design (Domain Objects)
**Implementation**: See `app/domain/entities/user.py`
- Private attributes with `_` prefix
- Public `@property` getters
- Business methods: `activate()`, `deactivate()`, `update_profile()`
- Inherit from `Entity` base class (provides UUID id)

### 5. Type Hints & Pydantic Settings
- **Strict typing**: Use `str | None` not `Optional[str]` (Python 3.10+ style)
- **Config validation**: See `app/core/config.py` - uses Pydantic v2 with `@field_validator`
- **Custom validators**: Enforce production secrets, token expiry limits, environment values

## Developer Workflows

### Commands (Windows PowerShell)
Use `.\commands.ps1 <command>` - see `commands.ps1` for full list:
- `dev` - Start with auto-reload (uvicorn)
- `migrate` - Apply Alembic migrations
- `docker-up` - Start PostgreSQL, Redis
- `test-cov` - Run pytest with HTML coverage report
- `format` - Black + Ruff auto-fix

### Migration Workflow
```bash
# Create migration after modifying models
poetry run alembic revision --autogenerate -m "add products table"

# Review generated migration in alembic/versions/
# Apply migration
poetry run alembic upgrade head
```

**Critical**: Alembic uses `DIRECT_URL` from settings (bypasses pgBouncer) - see `alembic/env.py` line 63

### Testing Pattern
**Setup**: See `tests/conftest.py`
- Separate test database: `hypertoq_test`
- `db_session` fixture auto-rollbacks
- Session-scoped `setup_database` creates/drops tables
```python
async def test_create_user(db_session):
    repo = UserRepository(db_session)
    # Test implementation
```

## Project-Specific Conventions

### 1. SQLAlchemy 2.0 Style (Type-Mapped Columns)
```python
from sqlalchemy.orm import Mapped, mapped_column
class UserModel(Base):
    email: Mapped[str] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
```

### 2. Base Model Mixins
**Location**: `app/infrastructure/database/base.py`
- `BaseModel`: UUID primary key + timestamps (created_at, updated_at)
- `SoftDeleteModel`: Adds is_deleted + deleted_at
- Use `BaseModel` for new tables instead of raw `Base`

### 3. FastAPI Response Models
Always use Pydantic DTOs for responses:
```python
@router.post("/users", response_model=UserResponseDTO)
async def create_user(data: UserCreateDTO):
    # Never return entity or SQLAlchemy model directly
    return service.create_user(data)
```

### 4. Error Handling
Raise `HTTPException` in services (not in repositories):
```python
if not user:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"  # Safe message for client
    )
```

### 5. Async Everywhere
- All database operations use `async/await`
- Session is `AsyncSession` from `sqlalchemy.ext.asyncio`
- Use `await session.execute(select(...))` not blocking queries

## External Integrations

### Google Gemini AI
**Location**: `app/infrastructure/external/gemini.py`
- Requires `GOOGLE_API_KEY` in `.env`
- Default model: `gemini-pro` (configurable via `GEMINI_MODEL`)

### LemonSqueezy Payments
**Location**: `app/infrastructure/external/lemonsqueezy.py`
- Requires: `LEMONSQUEEZY_API_KEY`, `STORE_ID`, `WEBHOOK_SECRET`

### Celery Background Tasks
**Config**: `app/core/celery_app.py`
- App name: `hypertroq`
- Start worker: `.\commands.ps1 celery-worker`
- Task definitions: `app/infrastructure/tasks.py`

## Security Implementation

### JWT Authentication
**Location**: `app/core/security.py` + `app/application/services/auth_service.py`
- Access token: 15 min expiry (configurable)
- Refresh token: 7 days (configurable)
- Uses `CurrentUserDep` dependency for protected routes

### Password Hashing
- Uses passlib with bcrypt
- Functions: `get_password_hash()`, `verify_password()`

## API Design Conventions

### Endpoint Structure
- Version prefix: `/api/v1/*`
- Plural nouns: `/exercises`, `/programs`, `/sessions`
- Resource hierarchy: `/programs/{program_id}/sessions/{session_id}`
- Actions as verbs: `/programs/{id}/clone`, `/programs/{id}/generate-schedule`
- Admin routes: `/api/v1/admin/*`

### Response Format
**Success**: `{"data": {...}, "meta": {"page": 1, "limit": 20, "total": 150, "has_more": true}}`
**Error**: `{"error": {"code": "VALIDATION_ERROR", "message": "...", "details": {...}, "timestamp": "...", "request_id": "..."}}`

### Field Conventions
- Use `snake_case` for JSON keys (Python convention)
- Dates in ISO 8601 format
- UUIDs as strings
- Enums as UPPERCASE strings

### Status Codes
- 200: Success (GET, PUT), 201: Created (POST), 204: No Content (DELETE)
- 400: Bad Request, 401: Unauthorized, 403: Forbidden, 404: Not Found
- 409: Conflict, 422: Unprocessable Entity, 429: Rate Limit, 500: Internal Error

### Pagination & Filtering
- Query params: `page` (1-indexed), `limit` (default 20, max 100)
- Filtering: `/exercises?equipment=BARBELL&muscle_group=CHEST`
- Search: `/exercises?search=bench+press`
- Sorting: `/programs?sort=created_at&order=desc`

## External Integrations

### Google Gemini AI (`app/infrastructure/external/gemini.py`)
- **Models**: `gemini-2.0-flash` (chatbot), `gemini-2.0-flash-lite` (high-volume), `text-embedding-004` (embeddings)
- **Usage**: Track tokens per organization, enforce rate limits by tier
- **Config**: Requires `GOOGLE_API_KEY`

### LemonSqueezy Payments (`app/infrastructure/external/lemonsqueezy.py`)
- **Endpoints**: Create checkout, handle webhooks at `/api/v1/webhooks/lemonsqueezy`
- **Security**: Verify webhook signatures with `LEMONSQUEEZY_WEBHOOK_SECRET`
- **Config**: Requires `LEMONSQUEEZY_API_KEY`, `STORE_ID`, `WEBHOOK_SECRET`

### Google Cloud Storage (app/core/storage.py)
- **Buckets**: `hypertoq-exercises` (public), `hypertoq-user-uploads` (private), `hypertoq-exports` (24hr retention)
- **Usage**: Exercise images/videos, profile pictures, CSV/PDF exports
- **Access**: Signed URLs for private files, public URLs for public content
- **Config**: Requires `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_STORAGE_BUCKET`

### Email Service (Future: SendGrid/Resend)
- **Use cases**: Welcome emails, verification, password reset, progress reports
- **Queue**: Send via Celery background tasks
- **Templates**: Store in `app/templates/emails/`

### Error Tracking & Monitoring
- **Sentry**: Backend + frontend error tracking, set `SENTRY_DSN`
- **Better Stack (Logtail)**: Centralized logging
- **Cloud Monitoring**: Metrics, uptime, alerts

### Celery Background Tasks (`app/infrastructure/tasks.py`)
- **Broker**: Redis (Celery uses `CELERY_BROKER_URL`)
- **Tasks**: Email sending, embedding generation, analytics aggregation, subscription sync, data exports
- **Retry**: 3 retries with exponential backoff
- **Commands**: `.\commands.ps1 celery-worker`, `.\commands.ps1 celery-beat`

## Testing Strategy

### Structure
```
tests/
├── unit/              # Pure logic (services, repositories, domain)
├── integration/       # API endpoint tests with TestClient
├── e2e/              # End-to-end scenarios (future - Playwright)
└── conftest.py       # Shared fixtures
```

### Unit Testing Patterns
**Coverage target**: >80% for business logic
**Key scenarios**:
```python
# Volume calculation
def test_calculate_muscle_volume():
    """Given: Exercise with chest=1.0, triceps=0.5
       When: User performs 3 sets
       Then: Chest gets 3 sets, triceps gets 1.5 sets"""

# Subscription checks
def test_custom_exercise_requires_pro():
    """Given: Free tier user
       When: Attempts to create custom exercise
       Then: Raise SubscriptionRequiredException"""
```

### Mocking External Services
```python
@pytest.fixture
def mock_gemini_api(mocker):
    return mocker.patch('app.services.gemini_service.genai')

@pytest.fixture
def mock_lemonsqueezy(mocker):
    return mocker.patch('app.services.payment_service.LemonSqueezy')
```

### Integration Testing
- Use `TestClient` from FastAPI
- Separate test database (`hypertoq_test`)
- Auto-rollback between tests (see `tests/conftest.py`)
- Test: Auth flow, authorization, CRUD, volume calculations, tier enforcement, webhooks

### Test Data
- **Fixtures**: Reusable test data in `conftest.py`
- **Factories**: Use factory_boy for model generation
- **Seed data**: Minimal exercises and templates
- **Cleanup**: Automatic rollback after each test

## Deployment Architecture

### Infrastructure (Google Cloud Platform)
```
Vercel (Frontend: Next.js) → Cloud Run (Backend: FastAPI)
                                    ↓
                     ┌──────────────┼──────────────┐
                     ↓              ↓              ↓
              Cloud SQL       Memorystore    Cloud Storage
             (PostgreSQL)       (Redis)         (Media)
```

### Cloud Run Configuration
- **Region**: `us-central1`
- **Resources**: 1 vCPU, 512 MB (scale to 2-4 vCPU, 1-2 GB)
- **Concurrency**: 80 requests/instance
- **Scaling**: Min 0 (cost-saving), Max 10
- **Timeout**: 300 seconds
- **Secrets**: Store in Secret Manager (DATABASE_URL, REDIS_URL, SECRET_KEY, API keys, SENTRY_DSN)

### Dockerfile Pattern
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD exec gunicorn --bind :$PORT --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 --access-logfile - app.main:app
```

### CI/CD (GitHub Actions)
**Pipeline**: `.github/workflows/backend-deploy.yml`
- Run tests on push to `main`
- Deploy to Cloud Run on success
- Frontend auto-deploys via Vercel GitHub integration

### Database (Cloud SQL)
- **Instance**: `db-f1-micro` (free tier start), PostgreSQL 16
- **Storage**: 10 GB SSD (auto-scaling)
- **Backups**: Daily automated, 7-day retention
- **Extensions**: `pgvector`, `uuid-ossp`
- **Connection**: Cloud SQL Proxy or Unix socket, SSL/TLS required
- **Format**: `postgresql+asyncpg://USER:PASSWORD@/DATABASE?host=/cloudsql/PROJECT:REGION:INSTANCE`
- **Migrations**: Run `alembic upgrade head` via Cloud Build

### Redis (Memorystore)
- **Tier**: Basic (1 GB start), Redis 7
- **Region**: Same as Cloud Run
- **Usage**: Sessions, API caching (5 min TTL), rate limiting, Celery queue

### Monitoring & Alerts
**Logs**: Structured JSON via Python `logging`, Cloud Logging (auto with Cloud Run)
**Metrics**: Request rate/latency (p50, p95, p99), error rate, DB pool usage, Redis hit/miss, Celery queue length
**Alerts**: Error rate >5%, p95 latency >1s, CPU >80% for 5 min, memory >90%, failed background jobs

### Security
- HTTPS only (TLS 1.3), CORS restricted to frontend domain
- Cloud Armor for DDoS protection
- VPC connector for private DB access
- Secrets in Secret Manager, rotate API keys quarterly
- GDPR-ready: data export, deletion, audit logging

## Common Pitfalls

1. **pgBouncer errors**: If seeing "prepared statement already exists", ensure using `DIRECT_URL` or `statement_cache_size=0`
2. **Circular imports**: Don't import `get_db()` in `app/core/__init__.py`
3. **Entity/Model confusion**: Entities (domain) vs Models (SQLAlchemy) - use Repository to convert
4. **Missing await**: All DB operations must be awaited
5. **Secret validation**: Settings class enforces production-safe secrets - avoid default values
6. **Volume calculation**: Always account for fractional muscle contributions (0.25, 0.5, 0.75, 1.0)
7. **Subscription checks**: Enforce tier restrictions in services before resource creation

## Key Files for Reference
- Architecture: `ARCHITECTURE.md`, `docs/PROJECT_SUMMARY.md`
- Database setup: `docs/DATABASE_SETUP.md`
- Example service: `app/application/services/user_service.py`
- Example repository: `app/infrastructure/repositories/user_repository.py`
- Config with validators: `app/core/config.py`
- Database manager: `app/infrastructure/database/connection.py`
