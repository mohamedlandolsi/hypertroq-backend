"""Test configuration and fixtures."""
import asyncio
from typing import AsyncGenerator, Any
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.infrastructure.database.base import Base
from app.main import app
from app.models.user import UserModel
from app.models.organization import OrganizationModel
from app.models.exercise import ExerciseModel
from app.core.dependencies import get_db


# Test database URL
TEST_DATABASE_URL = str(settings.DATABASE_URL).replace("/hypertroq", "/hypertroq_test")

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# Override get_db dependency for tests
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override database dependency for tests."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Create test database tables."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Drop all tables after tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests with automatic rollback."""
    async with TestSessionLocal() as session:
        # Start a transaction
        async with session.begin():
            yield session
            # Rollback after test to keep database clean
            await session.rollback()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide async HTTP client for API testing."""
    from httpx import ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
async def test_organization(db_session: AsyncSession) -> OrganizationModel:
    """Create a test organization."""
    from app.domain.value_objects.enums import SubscriptionTier, SubscriptionStatus
    
    org = OrganizationModel(
        name="Test Organization",
        subscription_tier=SubscriptionTier.FREE,
        subscription_status=SubscriptionStatus.ACTIVE,
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_pro_organization(db_session: AsyncSession) -> OrganizationModel:
    """Create a test PRO organization."""
    from app.domain.value_objects.enums import SubscriptionTier, SubscriptionStatus
    
    org = OrganizationModel(
        name="Test Pro Organization",
        subscription_tier=SubscriptionTier.PRO,
        subscription_status=SubscriptionStatus.ACTIVE,
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_user(
    db_session: AsyncSession, test_organization: OrganizationModel
) -> UserModel:
    """Create a test user."""
    from app.domain.value_objects.enums import UserRole
    
    user = UserModel(
        email="test@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Test User",
        role=UserRole.USER,
        organization_id=test_organization.id,
        is_verified=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(
    db_session: AsyncSession, test_organization: OrganizationModel
) -> UserModel:
    """Create a test admin user."""
    from app.domain.value_objects.enums import UserRole
    
    admin = UserModel(
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPassword123!"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        organization_id=test_organization.id,
        is_verified=True,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def test_unverified_user(
    db_session: AsyncSession, test_organization: OrganizationModel
) -> UserModel:
    """Create an unverified test user."""
    from app.domain.value_objects.enums import UserRole
    
    user = UserModel(
        email="unverified@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Unverified User",
        role=UserRole.USER,
        organization_id=test_organization.id,
        is_verified=False,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def user_token(test_user: UserModel) -> str:
    """Generate JWT access token for test user."""
    return create_access_token(
        subject={
            "user_id": str(test_user.id),
            "organization_id": str(test_user.organization_id),
            "role": str(test_user.role.value),
        }
    )


@pytest.fixture
def admin_token(test_admin: UserModel) -> str:
    """Generate JWT access token for test admin."""
    return create_access_token(
        subject={
            "user_id": str(test_admin.id),
            "organization_id": str(test_admin.organization_id),
            "role": str(test_admin.role.value),
        }
    )


@pytest.fixture
def user_refresh_token(test_user: UserModel) -> str:
    """Generate JWT refresh token for test user."""
    return create_refresh_token(
        subject={
            "user_id": str(test_user.id),
            "organization_id": str(test_user.organization_id),
            "role": str(test_user.role.value),
        }
    )


@pytest.fixture
async def test_global_exercises(db_session: AsyncSession) -> list[ExerciseModel]:
    """Create test global exercises."""
    from app.domain.value_objects.enums import EquipmentType
    
    exercises = [
        ExerciseModel(
            name="Barbell Bench Press",
            description="Compound chest exercise",
            equipment=EquipmentType.BARBELL,
            is_global=True,
            muscle_contributions={
                "CHEST": 1.0,
                "FRONT_DELTS": 0.5,
                "TRICEPS": 0.5,
            },
        ),
        ExerciseModel(
            name="Barbell Squat",
            description="Compound leg exercise",
            equipment=EquipmentType.BARBELL,
            is_global=True,
            muscle_contributions={
                "QUADS": 1.0,
                "GLUTES": 0.75,
                "HAMSTRINGS": 0.5,
            },
        ),
        ExerciseModel(
            name="Pull-ups",
            description="Bodyweight back exercise",
            equipment=EquipmentType.BODYWEIGHT,
            is_global=True,
            muscle_contributions={
                "LATS": 1.0,
                "TRAPS_RHOMBOIDS": 0.5,
                "ELBOW_FLEXORS": 0.5,
            },
        ),
    ]
    
    for exercise in exercises:
        db_session.add(exercise)
    
    await db_session.commit()
    
    for exercise in exercises:
        await db_session.refresh(exercise)
    
    return exercises


@pytest.fixture
def mock_redis(mocker):
    """Mock Redis client for tests."""
    mock = mocker.patch("app.infrastructure.cache.redis_client")
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    mock.exists.return_value = False
    return mock


@pytest.fixture
def mock_gemini(mocker):
    """Mock Google Gemini API for tests."""
    mock = mocker.patch("app.infrastructure.external.gemini.genai")
    mock.generate_content.return_value.text = "Mock AI response"
    return mock


@pytest.fixture
def mock_storage(mocker):
    """Mock Google Cloud Storage for tests."""
    mock = mocker.patch("app.core.storage.storage_client")
    mock.bucket.return_value.blob.return_value.public_url = "https://storage.googleapis.com/test/file.jpg"
    return mock


@pytest.fixture
def auth_headers(user_token: str) -> dict[str, str]:
    """Generate authorization headers with user token."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    """Generate authorization headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}
