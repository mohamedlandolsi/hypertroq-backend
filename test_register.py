"""Test registration endpoint."""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.connection import db_manager
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.services.auth_service import AuthService


async def test_register():
    """Test user registration."""
    try:
        # Test database connection
        print("Testing database connection...")
        await db_manager.test_connection()
        print("✓ Database connection successful")
        
        # Get session
        print("\nGetting database session...")
        session_maker = db_manager.get_session_maker()
        async with session_maker() as session:
            print("✓ Session created")
            
            # Create repositories
            print("\nCreating repositories...")
            user_repo = UserRepository(session)
            org_repo = OrganizationRepository(session)
            print("✓ Repositories created")
            
            # Create auth service
            print("\nCreating auth service...")
            auth_service = AuthService(user_repo, org_repo)
            print("✓ Auth service created")
            
            # Test registration
            print("\nTesting registration...")
            test_email = "test@example.com"
            
            # Check if user exists
            exists = await user_repo.exists_by_email(test_email)
            print(f"User exists: {exists}")
            
            if exists:
                print("User already exists, skipping registration test")
                return
            
            # Try registration
            result = await auth_service.register(
                email=test_email,
                password="TestPassword123!",
                full_name="Test User",
                organization_name="Test Organization"
            )
            
            print(f"✓ Registration successful!")
            print(f"Access token: {result.access_token[:50]}...")
            print(f"Refresh token: {result.refresh_token[:50]}...")
            
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_register())
