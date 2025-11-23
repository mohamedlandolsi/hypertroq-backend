# Database Architecture

Comprehensive database schema documentation for HypertroQ Backend.

## Table of Contents

- [Overview](#overview)
- [Database Schema](#database-schema)
- [Entity Relationships](#entity-relationships)
- [Table Definitions](#table-definitions)
- [Indexes](#indexes)
- [Constraints](#constraints)
- [Migrations](#migrations)
- [Query Optimization](#query-optimization)

---

## Overview

### Technology Stack

- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Connection Pool**: AsyncPG
- **Caching**: Redis 7

### Design Principles

1. **Normalization**: 3NF to minimize redundancy
2. **UUIDs**: Primary keys for distributed systems
3. **Timestamps**: Track created_at and updated_at
4. **Soft Deletes**: Preserve data with is_deleted flag
5. **JSON Columns**: Flexible data for muscle contributions
6. **Indexes**: Optimize common queries
7. **Foreign Keys**: Maintain referential integrity

---

## Database Schema

### ERD (Entity Relationship Diagram)

```
┌──────────────────┐
│  organizations   │
│  (multi-tenancy) │
└────────┬─────────┘
         │ 1
         │
         │ *
┌────────┴─────────┐         ┌──────────────────┐
│      users       │────────→│  training_       │
│                  │  1   *  │  programs        │
└────────┬─────────┘         └────────┬─────────┘
         │                            │
         │ *                          │ 1
         │                            │
         │                            │ *
         │                   ┌────────┴─────────┐
         │                   │  workout_        │
         └──────────────────→│  sessions        │
                 1        *  │                  │
                             └────────┬─────────┘
                                      │
                                      │ 1
                                      │
                                      │ *
┌──────────────────┐         ┌────────┴─────────┐
│    exercises     │←────────│  session_        │
│  (global + user) │  1   *  │  exercises       │
└──────────────────┘         └──────────────────┘
```

---

## Entity Relationships

### Organizations → Users (1:N)
- One organization has many users
- Users belong to one organization (multi-tenancy)

### Users → Training Programs (1:N)
- User can create multiple programs
- Each program belongs to one user

### Training Programs → Workout Sessions (1:N)
- Program contains multiple sessions (e.g., Push, Pull, Legs)
- Each session belongs to one program

### Workout Sessions → Session Exercises (1:N)
- Session contains multiple exercises
- Join table for many-to-many with additional data (sets, reps)

### Exercises → Session Exercises (1:N)
- Exercise can be used in multiple sessions
- Each session exercise references one exercise

### Users → Exercises (1:N)
- Users can create custom exercises (Pro tier)
- Global exercises have NULL created_by_user_id

---

## Table Definitions

### `organizations`

Multi-tenant organization table.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `name` | VARCHAR(255) | NOT NULL | Organization name |
| `slug` | VARCHAR(255) | UNIQUE, NOT NULL | URL-friendly identifier |
| `subscription_tier` | VARCHAR(50) | DEFAULT 'free' | Tier: free, pro, enterprise |
| `subscription_status` | VARCHAR(50) | DEFAULT 'active' | Status: active, cancelled, suspended |
| `ai_queries_used` | INTEGER | DEFAULT 0 | Monthly AI query count |
| `ai_queries_limit` | INTEGER | NULL | Max queries (NULL = unlimited for pro) |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**:
- `ix_organizations_slug` on `slug` (unique)

---

### `users`

User accounts and authentication.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `organization_id` | UUID | FK → organizations.id | Parent organization |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User email (login) |
| `hashed_password` | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| `full_name` | VARCHAR(255) | NOT NULL | User's full name |
| `is_active` | BOOLEAN | DEFAULT true | Account active status |
| `is_superuser` | BOOLEAN | DEFAULT false | Admin privileges |
| `subscription_tier` | VARCHAR(50) | DEFAULT 'free' | Tier: free, pro |
| `subscription_status` | VARCHAR(50) | DEFAULT 'active' | Status: active, cancelled, past_due |
| `ai_queries_used` | INTEGER | DEFAULT 0 | Monthly AI query count |
| `ai_queries_limit` | INTEGER | DEFAULT 10 | Max queries (10 for free, NULL for pro) |
| `email_verified` | BOOLEAN | DEFAULT false | Email verification status |
| `created_at` | TIMESTAMP | NOT NULL | Account creation |
| `updated_at` | TIMESTAMP | NOT NULL | Last update |

**Indexes**:
- `ix_users_email` on `email` (unique)
- `ix_users_organization_id` on `organization_id`

**Foreign Keys**:
- `organization_id` → `organizations.id` ON DELETE CASCADE

---

### `exercises`

Exercise library (global + user-created).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `name` | VARCHAR(255) | NOT NULL | Exercise name |
| `description` | TEXT | NULL | Exercise description |
| `equipment` | VARCHAR(50) | NOT NULL | Equipment: BARBELL, DUMBBELL, CABLE, etc. |
| `muscle_contributions` | JSON | NOT NULL | Muscle groups and contribution (0.25-1.0) |
| `difficulty` | VARCHAR(50) | DEFAULT 'INTERMEDIATE' | Difficulty: BEGINNER, INTERMEDIATE, ADVANCED |
| `is_global` | BOOLEAN | DEFAULT false | Global (admin) vs custom (user) |
| `created_by_user_id` | UUID | FK → users.id, NULL | Creator (NULL for global) |
| `image_url` | VARCHAR(500) | NULL | Exercise image URL |
| `video_url` | VARCHAR(500) | NULL | Exercise video URL |
| `embedding` | VECTOR(384) | NULL | AI embedding for semantic search |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update |

**Example muscle_contributions JSON**:
```json
{
  "CHEST": 1.0,
  "FRONT_DELTS": 0.5,
  "TRICEPS": 0.5
}
```

**Indexes**:
- `ix_exercises_name` on `name`
- `ix_exercises_is_global` on `is_global`
- `ix_exercises_created_by_user_id` on `created_by_user_id`
- `ix_exercises_equipment` on `equipment`

**Foreign Keys**:
- `created_by_user_id` → `users.id` ON DELETE SET NULL

---

### `training_programs`

User-created workout programs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK → users.id | Program owner |
| `name` | VARCHAR(255) | NOT NULL | Program name |
| `description` | TEXT | NULL | Program description |
| `structure_type` | VARCHAR(50) | NOT NULL | WEEKLY or CYCLIC |
| `frequency` | INTEGER | NOT NULL | Training days per week |
| `is_template` | BOOLEAN | DEFAULT false | Admin-created template |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update |

**Indexes**:
- `ix_programs_user_id` on `user_id`
- `ix_programs_is_template` on `is_template`

**Foreign Keys**:
- `user_id` → `users.id` ON DELETE CASCADE

---

### `workout_sessions`

Individual workout sessions within programs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `program_id` | UUID | FK → training_programs.id | Parent program |
| `name` | VARCHAR(255) | NOT NULL | Session name (e.g., "Push Day") |
| `day_of_week` | INTEGER | NULL | Day (0-6 for WEEKLY, NULL for CYCLIC) |
| `order_index` | INTEGER | NOT NULL | Session order in program |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update |

**Indexes**:
- `ix_sessions_program_id` on `program_id`

**Foreign Keys**:
- `program_id` → `training_programs.id` ON DELETE CASCADE

---

### `session_exercises`

Exercises within workout sessions (join table with data).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `session_id` | UUID | FK → workout_sessions.id | Parent session |
| `exercise_id` | UUID | FK → exercises.id | Exercise reference |
| `order_index` | INTEGER | NOT NULL | Exercise order in session |
| `sets` | INTEGER | NOT NULL | Number of sets |
| `reps` | VARCHAR(50) | NULL | Rep range (e.g., "8-12") |
| `rest_seconds` | INTEGER | NULL | Rest between sets |
| `notes` | TEXT | NULL | Exercise notes |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update |

**Indexes**:
- `ix_session_exercises_session_id` on `session_id`
- `ix_session_exercises_exercise_id` on `exercise_id`

**Foreign Keys**:
- `session_id` → `workout_sessions.id` ON DELETE CASCADE
- `exercise_id` → `exercises.id` ON DELETE RESTRICT

---

## Indexes

### Purpose

Indexes speed up queries at the cost of write performance and storage.

### Index Strategy

1. **Primary Keys**: Automatic B-tree index
2. **Foreign Keys**: Index for JOIN optimization
3. **Unique Constraints**: Automatic unique index
4. **Search Columns**: Index for WHERE, ORDER BY
5. **Composite Indexes**: For multi-column queries

### Current Indexes

```sql
-- Users
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_organization_id ON users(organization_id);

-- Exercises
CREATE INDEX ix_exercises_name ON exercises(name);
CREATE INDEX ix_exercises_is_global ON exercises(is_global);
CREATE INDEX ix_exercises_created_by_user_id ON exercises(created_by_user_id);
CREATE INDEX ix_exercises_equipment ON exercises(equipment);

-- Training Programs
CREATE INDEX ix_programs_user_id ON training_programs(user_id);
CREATE INDEX ix_programs_is_template ON training_programs(is_template);

-- Workout Sessions
CREATE INDEX ix_sessions_program_id ON workout_sessions(program_id);

-- Session Exercises
CREATE INDEX ix_session_exercises_session_id ON session_exercises(session_id);
CREATE INDEX ix_session_exercises_exercise_id ON session_exercises(exercise_id);
```

### Composite Index Example

For queries filtering by multiple columns:

```sql
-- Future optimization for exercise search
CREATE INDEX ix_exercises_global_equipment 
ON exercises(is_global, equipment) 
WHERE is_global = true;
```

---

## Constraints

### Primary Keys

All tables use `UUID` primary keys for:
- Distributed system compatibility
- No sequential ID exposure
- Merging data from multiple sources

### Foreign Keys

All foreign keys enforce referential integrity:
- `ON DELETE CASCADE`: Delete child when parent deleted
- `ON DELETE RESTRICT`: Prevent deletion if children exist
- `ON DELETE SET NULL`: Nullify FK when parent deleted

### Check Constraints

```sql
-- Frequency must be positive
ALTER TABLE training_programs 
ADD CONSTRAINT chk_frequency_positive 
CHECK (frequency > 0);

-- Sets must be positive
ALTER TABLE session_exercises 
ADD CONSTRAINT chk_sets_positive 
CHECK (sets > 0);

-- Day of week 0-6 or NULL
ALTER TABLE workout_sessions 
ADD CONSTRAINT chk_day_of_week_valid 
CHECK (day_of_week IS NULL OR (day_of_week >= 0 AND day_of_week <= 6));
```

### Unique Constraints

```sql
-- Email uniqueness (case-insensitive)
CREATE UNIQUE INDEX ix_users_email_lower ON users(LOWER(email));

-- Organization slug uniqueness
CREATE UNIQUE INDEX ix_organizations_slug ON organizations(slug);

-- Prevent duplicate exercises in same session at same position
CREATE UNIQUE INDEX ix_session_exercise_unique 
ON session_exercises(session_id, exercise_id, order_index);
```

---

## Migrations

### Alembic Configuration

Located in `alembic/` directory:
- `env.py`: Migration environment configuration
- `versions/`: Migration scripts

### Creating Migrations

```bash
# Auto-generate migration from model changes
poetry run alembic revision --autogenerate -m "add user_preferences table"

# Create empty migration
poetry run alembic revision -m "add custom index"
```

### Applying Migrations

```bash
# Apply all pending migrations
poetry run alembic upgrade head

# Apply specific migration
poetry run alembic upgrade <revision_id>

# Rollback one migration
poetry run alembic downgrade -1

# Rollback to specific version
poetry run alembic downgrade <revision_id>

# Reset database (⚠️ destroys data)
poetry run alembic downgrade base
```

### Migration Best Practices

1. **Review auto-generated migrations** - Alembic can't detect everything
2. **Test migrations locally** before production
3. **Backup production database** before migration
4. **Include both upgrade() and downgrade()** functions
5. **Use transactions** to ensure atomicity
6. **Avoid renaming columns** (drop + add is safer)

### Migration Example

```python
"""add user bio field

Revision ID: abc123
Revises: xyz789
Create Date: 2024-01-15 10:30:00

"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = 'xyz789'
branch_labels = None
depends_on = None

def upgrade():
    # Add column
    op.add_column('users', 
        sa.Column('bio', sa.String(500), nullable=True)
    )
    
    # Create index
    op.create_index('ix_users_bio', 'users', ['bio'])

def downgrade():
    # Drop index
    op.drop_index('ix_users_bio', table_name='users')
    
    # Drop column
    op.drop_column('users', 'bio')
```

---

## Query Optimization

### Common Query Patterns

#### 1. List Exercises with Pagination

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Optimized query with index usage
query = (
    select(ExerciseModel)
    .where(ExerciseModel.is_global == True)
    .where(ExerciseModel.equipment == "BARBELL")
    .order_by(ExerciseModel.name)
    .offset((page - 1) * limit)
    .limit(limit)
)

result = await session.execute(query)
exercises = result.scalars().all()
```

**Index used**: `ix_exercises_is_global`, `ix_exercises_equipment`

---

#### 2. Get Program with Sessions and Exercises

```python
# Eager load to avoid N+1 queries
query = (
    select(TrainingProgramModel)
    .where(TrainingProgramModel.id == program_id)
    .options(
        selectinload(TrainingProgramModel.sessions)
        .selectinload(WorkoutSessionModel.exercises)
        .selectinload(SessionExerciseModel.exercise)
    )
)

result = await session.execute(query)
program = result.scalar_one_or_none()
```

**Without eager loading**: 1 + N + M queries
**With eager loading**: 3-4 queries total

---

#### 3. Calculate Volume Per Muscle

```python
# Aggregate volume across program
query = (
    select(
        ExerciseModel.muscle_contributions,
        func.sum(SessionExerciseModel.sets)
    )
    .join(SessionExerciseModel, ExerciseModel.id == SessionExerciseModel.exercise_id)
    .join(WorkoutSessionModel, SessionExerciseModel.session_id == WorkoutSessionModel.id)
    .where(WorkoutSessionModel.program_id == program_id)
    .group_by(ExerciseModel.id)
)

result = await session.execute(query)
```

---

### Query Performance Tips

1. **Use indexes** for WHERE, JOIN, ORDER BY columns
2. **Eager load relationships** to avoid N+1 queries
3. **Paginate large result sets** with LIMIT and OFFSET
4. **Avoid SELECT \*** - specify needed columns
5. **Use database-level aggregation** instead of Python loops
6. **Cache frequently accessed data** in Redis

### EXPLAIN ANALYZE

Analyze query performance:

```sql
EXPLAIN ANALYZE
SELECT * FROM exercises
WHERE is_global = true
  AND equipment = 'BARBELL'
ORDER BY name
LIMIT 20;
```

Look for:
- **Index scans** (good) vs **Sequential scans** (slow for large tables)
- **Rows examined** vs **Rows returned** (should be similar)
- **Execution time** (target < 100ms for most queries)

---

## Database Maintenance

### Vacuum & Analyze

```sql
-- Reclaim space and update statistics
VACUUM ANALYZE;

-- Full vacuum (locks table)
VACUUM FULL;

-- Analyze specific table
ANALYZE exercises;
```

### Backup & Restore

```bash
# Backup (Cloud SQL)
gcloud sql backups create --instance=hypertroq-db

# Restore
gcloud sql backups restore BACKUP_ID \
  --backup-instance=hypertroq-db

# Manual backup (local)
pg_dump -U postgres -d hypertroq > backup.sql

# Restore
psql -U postgres -d hypertroq < backup.sql
```

### Monitoring

Key metrics to track:
- **Connection count**: Avoid pool exhaustion
- **Query duration**: p50, p95, p99 latency
- **Index usage**: Ensure indexes are being used
- **Table size**: Monitor growth
- **Cache hit ratio**: Target > 95%

---

## Future Enhancements

### Planned Tables

1. **`workout_logs`**: Track actual workouts performed
2. **`progress_photos`**: Store user progress photos
3. **`measurements`**: Body measurements over time
4. **`user_preferences`**: Store user settings
5. **`notifications`**: In-app notifications
6. **`audit_logs`**: Track changes for compliance

### Planned Indexes

```sql
-- Full-text search for exercises
CREATE INDEX ix_exercises_name_trgm 
ON exercises 
USING gin(name gin_trgm_ops);

-- Vector similarity search for embeddings
CREATE INDEX ix_exercises_embedding_cosine 
ON exercises 
USING ivfflat(embedding vector_cosine_ops);
```

---

## Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/16/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [pgvector for Embeddings](https://github.com/pgvector/pgvector)

---

**Database schema up to date as of**: January 2024
