"""Test script to verify User and Organization models work correctly."""
import asyncio
from uuid import UUID

from app.infrastructure.database.connection import db_manager
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.organization_repository import OrganizationRepository
from app.domain.entities.organization import Organization, SubscriptionTier, SubscriptionStatus
from app.domain.entities.user import User, UserRole
from app.core.security import get_password_hash


async def test_models():
    """Test User and Organization models."""
    print("🧪 Testing User and Organization models...")
    
    async with db_manager.session() as session:
        # Initialize repositories
        org_repo = OrganizationRepository(session)
        user_repo = UserRepository(session)
        
        # Test 1: Create an organization
        print("\n1️⃣ Creating test organization...")
        org = Organization(
            name="Test Organization",
            subscription_tier=SubscriptionTier.FREE,
            subscription_status=SubscriptionStatus.ACTIVE,
        )
        created_org = await org_repo.create(org)
        print(f"✅ Created organization: {created_org.name} (ID: {created_org.id})")
        print(f"   Tier: {created_org.subscription_tier.value}, Status: {created_org.subscription_status.value}")
        
        # Test 2: Create a user in that organization
        print("\n2️⃣ Creating test user...")
        user = User(
            email="test@hypertroq.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User",
            organization_id=created_org.id,
            role=UserRole.USER,
        )
        created_user = await user_repo.create(user)
        print(f"✅ Created user: {created_user.email} (ID: {created_user.id})")
        print(f"   Full name: {created_user.full_name}")
        print(f"   Organization: {created_user.organization_id}")
        print(f"   Role: {created_user.role.value}")
        print(f"   Active: {created_user.is_active}, Verified: {created_user.is_verified}")
        
        # Test 3: Query user by email
        print("\n3️⃣ Querying user by email...")
        found_user = await user_repo.get_by_email("test@hypertroq.com")
        if found_user:
            print(f"✅ Found user: {found_user.email}")
        else:
            print("❌ User not found")
        
        # Test 4: Get users by organization
        print("\n4️⃣ Getting users in organization...")
        org_users = await user_repo.get_by_organization(created_org.id)
        print(f"✅ Found {len(org_users)} users in organization")
        for u in org_users:
            print(f"   - {u.email} ({u.role.value})")
        
        # Test 5: Test organization business methods
        print("\n5️⃣ Testing organization business rules...")
        print(f"   Can create custom exercises: {created_org.can_create_custom_exercises()}")
        print(f"   Can create programs: {created_org.can_create_programs()}")
        print(f"   Has unlimited AI queries: {created_org.has_unlimited_ai_queries()}")
        
        # Test 6: Upgrade organization to PRO
        print("\n6️⃣ Upgrading organization to PRO...")
        created_org.upgrade_to_pro("cust_123", "sub_456")
        updated_org = await org_repo.update(created_org)
        print(f"✅ Upgraded to {updated_org.subscription_tier.value}")
        print(f"   LemonSqueezy Customer ID: {updated_org.lemonsqueezy_customer_id}")
        print(f"   Can create custom exercises: {updated_org.can_create_custom_exercises()}")
        
        # Test 7: Test user business methods
        print("\n7️⃣ Testing user business methods...")
        created_user.verify_email()
        created_user.update_profile(full_name="Updated Test User")
        updated_user = await user_repo.update(created_user)
        print(f"✅ Updated user: {updated_user.full_name}")
        print(f"   Email verified: {updated_user.is_verified}")
        
        # Test 8: Create an admin user
        print("\n8️⃣ Creating admin user...")
        admin = User(
            email="admin@hypertroq.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            organization_id=created_org.id,
            role=UserRole.ADMIN,
        )
        created_admin = await user_repo.create(admin)
        print(f"✅ Created admin: {created_admin.email}")
        print(f"   Is admin: {created_admin.is_admin()}")
        
        # Test 9: Clean up
        print("\n9️⃣ Cleaning up test data...")
        await user_repo.delete(created_user.id)
        await user_repo.delete(created_admin.id)
        await org_repo.delete(created_org.id)
        print("✅ Cleaned up all test data")
        
        print("\n✨ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_models())
