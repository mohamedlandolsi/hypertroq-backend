# Migration from Supabase to Google Cloud Services

## Overview
This document details the complete migration from Supabase to Google Cloud Platform services, completed on November 22, 2025.

## Changes Made

### 1. Database Migration
**From:** Supabase PostgreSQL  
**To:** Google Cloud SQL (PostgreSQL 16)

**Changes:**
- Updated `DATABASE_URL` format to Cloud SQL Unix socket connection
- Removed Supabase-specific connection strings from `.env.example`
- Added Cloud SQL format examples with `/cloudsql/` host path
- Kept all SQLAlchemy models and migrations intact (no code changes needed)
- Added pgvector support via Docker image (`pgvector/pgvector:pg16`)

**Connection String Format:**
```
# Production (Cloud SQL)
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@/DATABASE?host=/cloudsql/PROJECT:REGION:INSTANCE

# Local Development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/hypertroq
```

### 2. Authentication
**Status:** ✅ No Changes Required

Custom JWT authentication system (built in prompts 4-9) already in place:
- `app/core/security.py` - JWT token generation/validation
- `app/services/auth_service.py` - Complete auth service
- `app/api/v1/auth.py` - Auth endpoints
- `app/core/dependencies.py` - Auth dependencies

**Verification:**
- No Supabase Auth imports found
- All authentication uses custom implementation
- JWT tokens managed with `python-jose`
- Password hashing with `passlib[bcrypt]`

### 3. File Storage
**From:** Supabase Storage  
**To:** Google Cloud Storage

**New File:** `app/core/storage.py`

**Features:**
- `CloudStorageClient` class for all GCS operations
- `upload_file()` - Upload with optional public access
- `delete_file()` - Delete files from buckets
- `generate_signed_url()` - Temporary access URLs (configurable expiration)
- `file_exists()` - Check file existence
- `get_file_metadata()` - Retrieve file metadata

**Convenience Functions:**
- `upload_profile_image()` - User profile pictures
- `delete_profile_image()` - Remove profile pictures
- `upload_exercise_media()` - Exercise images/videos

**Bucket Structure:**
```
hypertroq-exercises/        # Public - exercise media
hypertroq-user-uploads/     # Private - user content
hypertroq-exports/          # Private - temporary exports (24hr retention)
```

### 4. Configuration Changes

#### `app/core/config.py`
**Removed:**
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`

**Added:**
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `GOOGLE_CLOUD_STORAGE_BUCKET` - Default storage bucket
- Validator for `GOOGLE_CLOUD_PROJECT` (production check)

#### `.env.example`
**Updated:**
- Replaced Supabase database examples with Cloud SQL format
- Removed all Supabase environment variables
- Added Google Cloud configuration section
- Reorganized sections for clarity

#### `pyproject.toml`
**Added:**
- `google-cloud-storage = "^2.10.0"`

**Note:** Run `poetry install` or `poetry update` to install new dependency.

#### `docker-compose.yml`
**Updated:**
- Changed PostgreSQL image from `postgres:16-alpine` to `pgvector/pgvector:pg16`
- Added `init-db.sql` mount for automatic extension installation
- Ensures pgvector available in local development

#### `init-db.sql` (New File)
**Purpose:** Initialize PostgreSQL with required extensions
- `vector` - Vector similarity search for AI embeddings
- `uuid-ossp` - UUID generation functions

### 5. Documentation Updates

#### `.github/copilot-instructions.md`
**Updated:**
- Changed "Supabase + pgBouncer" to "Google Cloud SQL + pgBouncer"
- Updated Cloud SQL connection documentation
- Added Google Cloud Storage section with bucket details
- Clarified Google Cloud services usage

## Verification Checklist

- ✅ All Supabase imports removed
- ✅ All Supabase environment variables removed
- ✅ Google Cloud Storage client implemented
- ✅ Configuration updated with Google Cloud settings
- ✅ Docker Compose uses pgvector image
- ✅ Database extensions setup script created
- ✅ Documentation updated
- ✅ Custom authentication preserved
- ✅ No code changes to models/migrations required

## Installation Steps

### 1. Install Dependencies
```bash
poetry install
# or
poetry update
```

### 2. Update Environment Variables
```bash
cp .env.example .env
# Edit .env and set:
# - DATABASE_URL
# - GOOGLE_CLOUD_PROJECT
# - GOOGLE_CLOUD_STORAGE_BUCKET
# - GOOGLE_API_KEY
```

### 3. Start Local Development
```bash
# Start Docker services (PostgreSQL + Redis)
docker-compose up -d postgres redis

# Run migrations
poetry run alembic upgrade head

# Start application
poetry run uvicorn app.main:app --reload
```

### 4. Google Cloud Setup (Production)

#### Cloud SQL
```bash
# Create instance
gcloud sql instances create hypertroq-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create hypertroq \
  --instance=hypertroq-db

# Enable extensions
gcloud sql connect hypertroq-db --user=postgres
> CREATE EXTENSION IF NOT EXISTS vector;
> CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

#### Cloud Storage
```bash
# Create buckets
gsutil mb -l us-central1 gs://hypertroq-exercises
gsutil mb -l us-central1 gs://hypertroq-user-uploads
gsutil mb -l us-central1 gs://hypertroq-exports

# Set public access for exercises bucket
gsutil iam ch allUsers:objectViewer gs://hypertroq-exercises

# Set lifecycle for exports (24hr retention)
cat > lifecycle.json << 'EOF'
{
  "lifecycle": {
    "rule": [{
      "action": {"type": "Delete"},
      "condition": {"age": 1}
    }]
  }
}
EOF
gsutil lifecycle set lifecycle.json gs://hypertroq-exports
```

## Testing

### Test Storage Operations
```python
from app.core.storage import storage_client

# Upload file
url = await storage_client.upload_file(
    file_content=b"Hello World",
    bucket_name="hypertroq-user-uploads",
    file_path="test/hello.txt",
    make_public=True
)
print(f"Uploaded: {url}")

# Generate signed URL
signed_url = await storage_client.generate_signed_url(
    bucket_name="hypertroq-user-uploads",
    file_path="test/hello.txt",
    expiration_minutes=60
)
print(f"Signed URL: {signed_url}")

# Delete file
success = await storage_client.delete_file(
    bucket_name="hypertroq-user-uploads",
    file_path="test/hello.txt"
)
print(f"Deleted: {success}")
```

### Test Authentication
```bash
# All auth endpoints still work with custom JWT system
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#",
    "full_name": "Test User",
    "organization_name": "Test Org"
  }'
```

## Breaking Changes

### None for Application Code
- All existing routes and services work without modification
- Database models unchanged
- Authentication logic unchanged
- API contracts preserved

### Environment Variables Required
New required environment variables:
- `GOOGLE_CLOUD_PROJECT` - Your GCP project ID
- `GOOGLE_CLOUD_STORAGE_BUCKET` - Default storage bucket name

### Removed Environment Variables
No longer needed (can be removed from `.env`):
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`

## Benefits

### Cost Optimization
- Google Cloud Free Tier: Cloud SQL (f1-micro), Cloud Storage, Cloud Run
- No Supabase subscription fees
- Pay-per-use for storage and compute

### Scalability
- Cloud SQL scales independently
- Cloud Storage handles unlimited files
- Cloud Run auto-scales based on traffic

### Integration
- Native integration with other Google Cloud services
- Unified billing and monitoring
- Better integration with Vertex AI / Gemini

### Control
- Full control over database configuration
- Custom backup strategies
- Direct access to storage buckets
- No vendor lock-in

## Rollback Plan

If issues arise, rollback is straightforward:

1. **Revert configuration files:**
   ```bash
   git revert <commit-hash>
   ```

2. **Restore Supabase connection:**
   - Update `DATABASE_URL` back to Supabase
   - Remove Google Cloud variables
   - Reinstall if needed

3. **Data migration:**
   - PostgreSQL dump/restore between services
   - Use `pg_dump` and `pg_restore`

## Support

### Google Cloud Documentation
- [Cloud SQL](https://cloud.google.com/sql/docs)
- [Cloud Storage](https://cloud.google.com/storage/docs)
- [Cloud Run](https://cloud.google.com/run/docs)

### Project-Specific
- See `docs/DATABASE_SETUP.md` for database configuration
- See `app/core/storage.py` for storage client usage
- See `.github/copilot-instructions.md` for architecture details

## Timeline

- **Migration Completed:** November 22, 2025
- **Testing Phase:** 1-2 weeks
- **Production Deployment:** TBD

## Contributors

- Migration executed by: AI Assistant
- Reviewed by: Development Team
- Approved by: Project Owner
