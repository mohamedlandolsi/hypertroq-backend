# Testing Infrastructure

Comprehensive test suite for HypertroQ Backend using pytest and pytest-asyncio.

## Overview

This test suite includes:
- **Unit tests** for business logic and utilities
- **Integration tests** for API endpoints and database operations
- **Authentication tests** for security and token management
- **Authorization tests** for role-based access control
- **Volume calculation tests** for hypertrophy tracking

## Structure

```
tests/
├── conftest.py           # Shared fixtures and test configuration
├── test_auth.py          # Authentication and authorization tests
├── test_exercises.py     # Exercise CRUD and filtering tests
├── test_programs.py      # Training program management tests
├── test_admin.py         # Admin functionality tests
├── __init__.py
└── README.md            # This file
```

## Test Database

Tests use a separate database (`hypertroq_test`) to avoid affecting development/production data.

**Database URL**: `postgresql+asyncpg://postgres:postgres@localhost:5433/hypertroq_test`

The test database is automatically created and torn down for each test session.

## Fixtures

### Core Fixtures (conftest.py)

#### Database Fixtures
- `setup_database`: Session-scoped fixture that creates/drops all tables
- `db_session`: Function-scoped session with automatic rollback
- `async_client`: AsyncClient for making HTTP requests to the API

#### User Fixtures
- `test_user`: Regular user (FREE tier, verified, active)
- `test_admin`: Admin user (FREE tier, verified, active)
- `test_unverified_user`: Unverified user
- `user_token`: JWT access token for test_user
- `admin_token`: JWT access token for test_admin
- `user_refresh_token`: JWT refresh token for test_user
- `auth_headers`: Authorization headers with user token
- `admin_headers`: Authorization headers with admin token

#### Organization Fixtures
- `test_organization`: FREE tier organization
- `test_pro_organization`: PRO tier organization

#### Exercise Fixtures
- `test_global_exercises`: 3 global exercises (Bench Press, Squat, Pull-ups)

#### Mock Fixtures
- `mock_redis`: Mocked Redis client
- `mock_gemini`: Mocked Google Gemini AI API
- `mock_storage`: Mocked Google Cloud Storage

## Running Tests

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Test File
```bash
python -m pytest tests/test_auth.py -v
```

### Run Specific Test Class
```bash
python -m pytest tests/test_auth.py::TestRegistration -v
```

### Run Specific Test Method
```bash
python -m pytest tests/test_auth.py::TestRegistration::test_register_success -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term
```

### Run with Specific Markers
```bash
# Run only integration tests
python -m pytest tests/ -m integration -v

# Run only unit tests
python -m pytest tests/ -m unit -v

# Run only slow tests
python -m pytest tests/ -m slow -v
```

### Debugging Failed Tests
```bash
# Show local variables on failure
python -m pytest tests/ -v --showlocals

# Stop at first failure
python -m pytest tests/ -v -x

# Drop into debugger on failure
python -m pytest tests/ -v --pdb

# Only run failed tests from last run
python -m pytest tests/ --lf
```

## Test Categories

### Authentication Tests (`test_auth.py`)

#### TestRegistration
- ✅ Successful user registration
- ✅ Duplicate email rejection
- ✅ Weak password validation
- ✅ Invalid email format validation

#### TestLogin
- ✅ Successful login
- ✅ Wrong password rejection
- ✅ Non-existent user rejection
- ✅ Inactive user rejection

#### TestTokenRefresh
- ✅ Successful token refresh
- ✅ Access token rejected for refresh
- ✅ Invalid token rejection

#### TestGetCurrentUser
- ✅ Get user with valid token
- ✅ No token rejection
- ✅ Invalid token rejection

#### TestPasswordReset
- ✅ Request password reset (with user enumeration protection)
- ✅ Confirm password reset with valid token
- ✅ Invalid token rejection

#### TestEmailVerification
- ✅ Verify email with valid token
- ✅ Invalid token rejection

#### TestAuthenticationMiddleware
- ✅ Protected routes require authentication
- ✅ Expired tokens rejected
- ✅ Malformed tokens rejected
- ✅ Missing Bearer prefix rejected

### Exercise Tests (`test_exercises.py`)

#### TestExerciseList
- ✅ List global exercises
- ✅ Authentication required
- ✅ Pagination support

#### TestExerciseFiltering
- ✅ Filter by equipment type
- ✅ Filter by muscle group
- ✅ Search by name
- ✅ Multiple filters combined

#### TestExerciseCreate
- ✅ FREE tier cannot create custom exercises
- ✅ PRO tier can create custom exercises
- ✅ Invalid muscle contribution validation
- ✅ Duplicate name rejection

#### TestExerciseRetrieve
- ✅ Get exercise by ID
- ✅ Non-existent exercise returns 404

#### TestExerciseUpdate
- ✅ Non-admin cannot update global exercises
- ✅ Admin can update global exercises

#### TestExerciseDelete
- ✅ Non-admin cannot delete global exercises
- ✅ Admin can delete global exercises

#### TestMuscleVolumeCalculations
- ✅ Full muscle contribution (1.0)
- ✅ Partial muscle contribution (0.5, 0.75)
- ✅ Multiple exercises volume aggregation
- ✅ Volume calculation API endpoint

### Program Tests (`test_programs.py`)

#### TestProgramList
- ✅ List program templates
- ✅ List user programs
- ✅ Filter by split type

#### TestProgramCreate
- ✅ FREE tier cannot create programs
- ✅ PRO tier can create programs
- ✅ Invalid structure validation

#### TestProgramClone
- ✅ Clone template successfully
- ✅ Non-existent template rejection
- ✅ Clone with modifications

#### TestSessionManagement
- ✅ Add session to program
- ✅ Update session
- ✅ Delete session

#### TestVolumeCalculations
- ✅ Calculate total program volume
- ✅ Volume by muscle group
- ✅ Weekly volume calculation

#### TestScheduleGeneration
- ✅ Generate weekly schedule
- ✅ Schedule respects program structure

#### TestProgramRetrieve
- ✅ Get program by ID
- ✅ Get program with sessions

#### TestProgramUpdate
- ✅ Update user's own program
- ✅ Cannot update templates (non-admin)

#### TestProgramDelete
- ✅ Delete user's own program
- ✅ Cannot delete templates (non-admin)

### Admin Tests (`test_admin.py`)

#### TestAdminAuthorization
- ✅ Admin endpoints require admin role
- ✅ Admin users can access admin endpoints
- ✅ Admin endpoints require authentication

#### TestUserManagement
- ✅ List all users
- ✅ Search users by email
- ✅ Get user by ID
- ✅ Update user information
- ✅ Deactivate user
- ✅ Activate user
- ✅ Delete user
- ✅ Change user role

#### TestOrganizationManagement
- ✅ List all organizations
- ✅ Get organization by ID
- ✅ Update organization subscription
- ✅ Get organization users
- ✅ Get organization statistics

#### TestGlobalResourceManagement
- ✅ Create global exercise
- ✅ Update global exercise
- ✅ Delete global exercise
- ✅ Create program template
- ✅ Update program template
- ✅ Delete program template

#### TestAdminStatistics
- ✅ Platform-wide statistics
- ✅ User growth statistics
- ✅ Subscription distribution

#### TestAdminBulkOperations
- ✅ Bulk update users
- ✅ Bulk delete inactive users

## Mocking Strategy

### External Services

All external services are mocked to ensure tests are:
- **Fast**: No network calls
- **Reliable**: No external dependencies
- **Deterministic**: Consistent results

#### Redis
```python
def test_with_redis(mock_redis):
    # Redis is automatically mocked
    mock_redis.get.return_value = "cached_value"
```

#### Google Gemini AI
```python
def test_with_gemini(mock_gemini):
    # Gemini API is automatically mocked
    mock_gemini.generate_content.return_value.text = "AI response"
```

#### Google Cloud Storage
```python
def test_with_storage(mock_storage):
    # Storage is automatically mocked
    mock_storage.bucket.return_value.blob.return_value.public_url = "https://..."
```

## Best Practices

### 1. Use Fixtures for Setup
```python
@pytest.mark.asyncio
async def test_example(db_session, test_user, auth_headers):
    # Use fixtures instead of manual setup
    pass
```

### 2. Test Both Success and Failure
```python
async def test_success_case(...):
    # Test happy path
    pass

async def test_failure_case(...):
    # Test error handling
    pass
```

### 3. Verify Database Changes
```python
async def test_update(db_session, test_user):
    # Make update
    response = await client.put(...)
    
    # Verify in database
    await db_session.refresh(test_user)
    assert test_user.full_name == "Updated Name"
```

### 4. Test Authorization
```python
async def test_requires_admin(auth_headers):
    # Regular user should be forbidden
    response = await client.get("/admin/...", headers=auth_headers)
    assert response.status_code == 403
```

### 5. Use Descriptive Test Names
```python
# Good
async def test_free_tier_cannot_create_custom_exercises(...):
    pass

# Bad
async def test_exercise(...):
    pass
```

## Common Assertions

### Status Codes
```python
assert response.status_code == 200  # Success
assert response.status_code == 201  # Created
assert response.status_code == 400  # Bad Request
assert response.status_code == 401  # Unauthorized
assert response.status_code == 403  # Forbidden
assert response.status_code == 404  # Not Found
assert response.status_code == 422  # Validation Error
```

### Response Structure
```python
data = response.json()
assert "data" in data
assert "meta" in data
assert len(data["data"]) > 0
```

### Token Validation
```python
from app.core.security import decode_token

payload = decode_token(token)
assert payload["type"] == "access"
assert "user_id" in payload
```

## Troubleshooting

### Database Connection Issues
```bash
# Ensure PostgreSQL is running
docker ps | grep hypertoq-postgres

# Ensure test database exists
docker exec hypertoq-postgres psql -U postgres -c "CREATE DATABASE hypertroq_test;"
```

### Import Errors
```bash
# Ensure you're in the project root
cd d:\MyProject\hypertroq\hypertroq-backend

# Run tests with Python module syntax
python -m pytest tests/
```

### Async Fixture Issues
```python
# Use @pytest.fixture for async fixtures (pytest-asyncio 1.x)
@pytest.fixture
async def my_async_fixture():
    # Setup
    yield value
    # Teardown
```

### Slow Tests
```bash
# Profile test execution time
python -m pytest tests/ --durations=10

# Run only fast tests
python -m pytest tests/ -m "not slow"
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5433:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov pytest-mock
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5433/hypertroq_test
        run: |
          pytest tests/ --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Performance Benchmarks

Target test execution times:
- **Unit tests**: < 100ms each
- **Integration tests**: < 500ms each
- **Full suite**: < 60 seconds

Current metrics:
- Total tests: 100+
- Coverage: >80% (target)
- Execution time: ~30 seconds (with mocks)

## Future Improvements

- [ ] Add mutation testing with `mutmut`
- [ ] Add property-based testing with `hypothesis`
- [ ] Add API contract testing with `schemathesis`
- [ ] Add load testing with `locust`
- [ ] Add E2E tests with `playwright`
- [ ] Add visual regression testing
- [ ] Add security testing with `safety` and `bandit`

## Contributing

When adding new tests:
1. Follow existing naming conventions
2. Add docstrings to test classes and methods
3. Use appropriate fixtures
4. Mock external services
5. Test both success and failure cases
6. Verify database state changes
7. Update this README if adding new test categories

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
