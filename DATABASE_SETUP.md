# Database Setup Documentation

## Overview

The database layer for HypertroQ backend is built using PostgreSQL 16 with SQLAlchemy 2.0 async support and Alembic for migrations.

## Components

### 1. Database Connection (`app/infrastructure/database/connection.py`)

**DatabaseManager Class:**
- Manages async database engine and session creation
- Connection pooling with configurable settings
- Health checks with `pool_pre_ping`
- Graceful shutdown handling

**Key Functions:**
- `get_db()`: FastAPI dependency for database sessions
- `init_database()`: Initialize database on app startup
- `close_database()`: Close connections on app shutdown

**Configuration:**
- Engine: AsyncEngine with asyncpg driver
- Pool Size: Configurable (default: 20)
- Max Overflow: Configurable (default: 0)
- Pool Recycle: 3600 seconds (1 hour)
- Connection Timeout: 30 seconds

### 2. Base Classes (`app/infrastructure/database/base.py`)

**Mixins:**
- `UUIDMixin`: UUID primary key with automatic generation
- `TimestampMixin`: created_at and updated_at timestamps with server defaults
- `SoftDeleteMixin`: Soft delete functionality with is_deleted flag and deleted_at timestamp

**Abstract Base Classes:**
- `BaseModel`: Combines UUID + Timestamps, includes `to_dict()` and `__repr__()`
- `SoftDeleteModel`: Full-featured model with all mixins

**Features:**
- Automatic table name generation (snake_case)
- Server-side default timestamps
- Type hints with SQLAlchemy 2.0 mapped columns
- Soft delete with restore() method

### 3. Alembic Configuration

**Setup:**
- Async migrations support
- Automatic model detection
- Project root added to Python path for imports
- Database URL from settings

**Migration Files:**
- Initial migration: `ddef93c02177_initial_migration_with_user_model.py`
- Includes users table with all fields and indexes

## Database Schema

### Users Table

| Column          | Type         | Constraints          | Description                    |
|-----------------|--------------|----------------------|--------------------------------|
| id              | UUID         | PRIMARY KEY          | Auto-generated UUID            |
| email           | VARCHAR(255) | UNIQUE, NOT NULL     | User email (indexed)           |
| hashed_password | VARCHAR(255) | NOT NULL             | Bcrypt hashed password         |
| full_name       | VARCHAR(255) | NULL                 | User's full name               |
| is_active       | BOOLEAN      | NOT NULL, DEFAULT TRUE | Active status                |
| is_superuser    | BOOLEAN      | NOT NULL, DEFAULT FALSE | Admin status                |
| created_at      | TIMESTAMPTZ  | NOT NULL, DEFAULT now() | Creation timestamp          |
| updated_at      | TIMESTAMPTZ  | NOT NULL, DEFAULT now() | Last update timestamp       |

**Indexes:**
- `users_pkey`: Primary key on id
- `ix_users_email`: Unique index on email
- `ix_users_id`: Index on id

## Connection Details

### Docker PostgreSQL

- **Image:** postgres:16-alpine
- **Container:** hypertoq-postgres
- **Host Port:** 5433 (mapped to avoid conflict with local PostgreSQL)
- **Container Port:** 5432
- **Database:** hypertoq
- **User:** postgres
- **Password:** postgres

### Connection String

```
postgresql+asyncpg://postgres:postgres@localhost:5433/hypertoq
```

## Usage Examples

### Using Database Session in Routes

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel))
    return result.scalars().all()
```

### Creating a Model with BaseModel

```python
from app.infrastructure.database.base import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

class Product(BaseModel):
    __tablename__ = "products"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    # id, created_at, updated_at inherited from BaseModel
```

### Using Soft Delete

```python
from app.infrastructure.database.base import SoftDeleteModel

class Order(SoftDeleteModel):
    __tablename__ = "orders"
    
    # Your fields here
    
# Soft delete
await order.soft_delete(db)

# Restore
await order.restore(db)

# Query only non-deleted
result = await db.execute(
    select(Order).where(Order.is_deleted == False)
)
```

## Migration Commands

### Create a New Migration

```bash
poetry run alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
poetry run alembic upgrade head
```

### Rollback Last Migration

```bash
poetry run alembic downgrade -1
```

### View Migration History

```bash
poetry run alembic history
```

### Check Current Migration

```bash
poetry run alembic current
```

## Troubleshooting

### Port Conflict with Local PostgreSQL

If you have a local PostgreSQL service running on port 5432, the Docker container is configured to use port 5433 instead. Update your DATABASE_URL in `.env`:

```
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5433/hypertoq"
```

### AsyncPG Installation Issues

If asyncpg fails to build (Windows C++ compiler required), version 0.30.0 includes pre-built wheels for Python 3.13:

```bash
poetry add asyncpg --allow-prereleases
```

### Circular Import Issues

Database dependencies use lazy imports to avoid circular imports. If you encounter circular import errors, ensure `get_db()` is not imported at module level in `app/core/__init__.py`.

## Performance Considerations

### Connection Pooling

- Default pool size: 20 connections
- Adjust `DB_POOL_SIZE` in settings for high-traffic scenarios
- Use `DB_MAX_OVERFLOW` for burst capacity

### Query Optimization

- Use indexes on frequently queried fields
- Implement proper pagination for large datasets
- Use `select()` with specific columns instead of `SELECT *`
- Leverage asyncio for concurrent queries

### Monitoring

- Enable `DB_ECHO=True` in development to log SQL queries
- Monitor connection pool usage
- Track slow queries with PostgreSQL logs

## Security Best Practices

1. **Never** commit `.env` with production credentials
2. Use strong, unique passwords for production databases
3. Enable SSL for database connections in production
4. Regularly update dependencies for security patches
5. Use read-only database users for query-only operations
6. Implement connection timeout and retry logic

## Next Steps

1. Implement repository pattern for data access
2. Add database seeding for development
3. Set up automated backups
4. Configure database monitoring and alerting
5. Implement database connection pooling optimization
6. Add query performance logging
