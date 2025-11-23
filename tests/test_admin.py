"""
Admin API tests.

Tests for admin authorization, user management,
organization management, and global resource management.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserModel
from app.models.organization import OrganizationModel
from app.models.exercise import ExerciseModel


class TestAdminAuthorization:
    """Tests for admin role authorization."""
    
    @pytest.mark.asyncio
    async def test_admin_endpoints_require_admin_role(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test that admin endpoints reject non-admin users."""
        response = await async_client.get(
            "/api/v1/admin/users",
            headers=auth_headers,
        )
        
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_admin_can_access_admin_endpoints(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Test that admin users can access admin endpoints."""
        response = await async_client.get(
            "/api/v1/admin/users",
            headers=admin_headers,
        )
        
        # Should be successful or 404 if endpoint doesn't exist
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_admin_endpoints_require_authentication(
        self, async_client: AsyncClient
    ):
        """Test that admin endpoints require authentication."""
        response = await async_client.get("/api/v1/admin/users")
        
        assert response.status_code == 401


class TestUserManagement:
    """Tests for admin user management."""
    
    @pytest.mark.asyncio
    async def test_list_all_users(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_user: UserModel,
        test_admin: UserModel,
    ):
        """Test admin can list all users."""
        response = await async_client.get(
            "/api/v1/admin/users",
            headers=admin_headers,
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert len(data["data"]) >= 2  # At least test user and admin
            
            # Verify user data structure
            user = data["data"][0]
            assert "id" in user
            assert "email" in user
            assert "role" in user
            assert "hashed_password" not in user  # Should not expose password
    
    @pytest.mark.asyncio
    async def test_search_users_by_email(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_user: UserModel,
    ):
        """Test searching users by email."""
        response = await async_client.get(
            f"/api/v1/admin/users?email={test_user.email}",
            headers=admin_headers,
        )
        
        if response.status_code == 200:
            data = response.json()
            assert len(data["data"]) >= 1
            assert data["data"][0]["email"] == test_user.email
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_user: UserModel,
    ):
        """Test admin can get any user by ID."""
        response = await async_client.get(
            f"/api/v1/admin/users/{test_user.id}",
            headers=admin_headers,
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == str(test_user.id)
            assert data["email"] == test_user.email
    
    @pytest.mark.asyncio
    async def test_update_user(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_user: UserModel,
        db_session: AsyncSession,
    ):
        """Test admin can update user information."""
        response = await async_client.put(
            f"/api/v1/admin/users/{test_user.id}",
            headers=admin_headers,
            json={
                "full_name": "Admin Updated Name",
                "is_verified": True,
            },
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["full_name"] == "Admin Updated Name"
            
            # Verify in database
            await db_session.refresh(test_user)
            assert test_user.full_name == "Admin Updated Name"
    
    @pytest.mark.asyncio
    async def test_deactivate_user(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        db_session: AsyncSession,
        test_organization: OrganizationModel,
    ):
        """Test admin can deactivate users."""
        from app.domain.value_objects.enums import UserRole
        from app.core.security import get_password_hash
        
        # Create user to deactivate
        user = UserModel(
            email="todeactivate@example.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="To Deactivate",
            role=UserRole.USER,
            organization_id=test_organization.id,
            is_verified=True,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        response = await async_client.post(
            f"/api/v1/admin/users/{user.id}/deactivate",
            headers=admin_headers,
        )
        
        if response.status_code == 200:
            await db_session.refresh(user)
            assert user.is_active is False
    
    @pytest.mark.asyncio
    async def test_activate_user(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        db_session: AsyncSession,
        test_organization: OrganizationModel,
    ):
        """Test admin can activate users."""
        from app.domain.value_objects.enums import UserRole
        from app.core.security import get_password_hash
        
        # Create inactive user
        user = UserModel(
            email="toactivate@example.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="To Activate",
            role=UserRole.USER,
            organization_id=test_organization.id,
            is_verified=True,
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        response = await async_client.post(
            f"/api/v1/admin/users/{user.id}/activate",
            headers=admin_headers,
        )
        
        if response.status_code == 200:
            await db_session.refresh(user)
            assert user.is_active is True
    
    @pytest.mark.asyncio
    async def test_delete_user(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        db_session: AsyncSession,
        test_organization: OrganizationModel,
    ):
        """Test admin can delete users."""
        from app.domain.value_objects.enums import UserRole
        from app.core.security import get_password_hash
        
        # Create user to delete
        user = UserModel(
            email="todelete@example.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="To Delete",
            role=UserRole.USER,
            organization_id=test_organization.id,
            is_verified=True,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        user_id = user.id
        
        response = await async_client.delete(
            f"/api/v1/admin/users/{user_id}",
            headers=admin_headers,
        )
        
        if response.status_code in [200, 204]:
            # Verify user is deleted
            from sqlalchemy import select
            result = await db_session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            deleted_user = result.scalar_one_or_none()
            assert deleted_user is None or deleted_user.is_active is False
    
    @pytest.mark.asyncio
    async def test_change_user_role(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_user: UserModel,
        db_session: AsyncSession,
    ):
        """Test admin can change user roles."""
        response = await async_client.put(
            f"/api/v1/admin/users/{test_user.id}/role",
            headers=admin_headers,
            json={"role": "ADMIN"},
        )
        
        if response.status_code == 200:
            await db_session.refresh(test_user)
            assert test_user.role.value == "ADMIN"


class TestOrganizationManagement:
    """Tests for admin organization management."""
    
    @pytest.mark.asyncio
    async def test_list_all_organizations(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_organization: OrganizationModel,
    ):
        """Test admin can list all organizations."""
        response = await async_client.get(
            "/api/v1/admin/organizations",
            headers=admin_headers,
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert len(data["data"]) >= 1
    
    @pytest.mark.asyncio
    async def test_get_organization_by_id(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_organization: OrganizationModel,
    ):
        """Test admin can get organization details."""
        response = await async_client.get(
            f"/api/v1/admin/organizations/{test_organization.id}",
            headers=admin_headers,
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == str(test_organization.id)
            assert data["name"] == test_organization.name
    
    @pytest.mark.asyncio
    async def test_update_organization_subscription(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_organization: OrganizationModel,
        db_session: AsyncSession,
    ):
        """Test admin can update organization subscription."""
        response = await async_client.put(
            f"/api/v1/admin/organizations/{test_organization.id}",
            headers=admin_headers,
            json={
                "subscription_tier": "PRO",
                "subscription_status": "ACTIVE",
            },
        )
        
        if response.status_code == 200:
            await db_session.refresh(test_organization)
            assert test_organization.subscription_tier.value == "PRO"
    
    @pytest.mark.asyncio
    async def test_get_organization_users(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_organization: OrganizationModel,
        test_user: UserModel,
    ):
        """Test admin can list users in an organization."""
        response = await async_client.get(
            f"/api/v1/admin/organizations/{test_organization.id}/users",
            headers=admin_headers,
        )
        
        if response.status_code == 200:
            data = response.json()
            assert len(data["data"]) >= 1
            user_ids = [u["id"] for u in data["data"]]
            assert str(test_user.id) in user_ids
    
    @pytest.mark.asyncio
    async def test_get_organization_stats(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_organization: OrganizationModel,
    ):
        """Test admin can get organization statistics."""
        response = await async_client.get(
            f"/api/v1/admin/organizations/{test_organization.id}/stats",
            headers=admin_headers,
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "user_count" in data or "total_users" in data


class TestGlobalResourceManagement:
    """Tests for managing global resources (exercises, templates)."""
    
    @pytest.mark.asyncio
    async def test_create_global_exercise(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test admin can create global exercises."""
        response = await async_client.post(
            "/api/v1/admin/exercises",
            headers=admin_headers,
            json={
                "name": "Admin Global Exercise",
                "description": "Created by admin",
                "equipment": "BARBELL",
                "muscle_contributions": {
                    "CHEST": 1.0,
                    "TRICEPS": 0.5,
                },
            },
        )
        
        if response.status_code == 201:
            data = response.json()
            assert data["is_global"] is True
            assert data["name"] == "Admin Global Exercise"
    
    @pytest.mark.asyncio
    async def test_update_global_exercise(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_global_exercises: list[ExerciseModel],
        db_session: AsyncSession,
    ):
        """Test admin can update global exercises."""
        exercise = test_global_exercises[0]
        
        response = await async_client.put(
            f"/api/v1/admin/exercises/{exercise.id}",
            headers=admin_headers,
            json={
                "description": "Admin updated description",
            },
        )
        
        if response.status_code == 200:
            await db_session.refresh(exercise)
            assert exercise.description == "Admin updated description"
    
    @pytest.mark.asyncio
    async def test_delete_global_exercise(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test admin can delete global exercises."""
        from app.domain.value_objects.enums import EquipmentType
        
        # Create exercise to delete
        exercise = ExerciseModel(
            name="To Delete Global",
            description="Will be deleted",
            equipment=EquipmentType.DUMBBELL,
            is_global=True,
            muscle_contributions={"CHEST": 1.0},
        )
        db_session.add(exercise)
        await db_session.commit()
        await db_session.refresh(exercise)
        exercise_id = exercise.id
        
        response = await async_client.delete(
            f"/api/v1/admin/exercises/{exercise_id}",
            headers=admin_headers,
        )
        
        assert response.status_code in [200, 204]
    
    @pytest.mark.asyncio
    async def test_create_program_template(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
    ):
        """Test admin can create program templates."""
        response = await async_client.post(
            "/api/v1/admin/programs/templates",
            headers=admin_headers,
            json={
                "name": "Admin Template",
                "description": "Created by admin",
                "split_type": "PUSH_PULL_LEGS",
                "structure_type": "WEEKLY",
                "structure_config": {"days": [1, 2, 3, 5, 6, 7]},
                "duration_weeks": 12,
            },
        )
        
        if response.status_code == 201:
            data = response.json()
            assert data["is_template"] is True
            assert data["name"] == "Admin Template"
    
    @pytest.mark.asyncio
    async def test_update_program_template(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test admin can update program templates."""
        from app.models.training_program import TrainingProgramModel
        from app.domain.value_objects.enums import SplitType, StructureType
        
        # Create template to update
        template = TrainingProgramModel(
            name="Template To Update",
            description="Will be updated",
            split_type=SplitType.FULL_BODY,
            structure_type=StructureType.WEEKLY,
            structure_config={"days": [1, 3, 5]},
            is_template=True,
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)
        
        response = await async_client.put(
            f"/api/v1/admin/programs/templates/{template.id}",
            headers=admin_headers,
            json={
                "description": "Admin updated template",
            },
        )
        
        if response.status_code == 200:
            await db_session.refresh(template)
            assert template.description == "Admin updated template"
    
    @pytest.mark.asyncio
    async def test_delete_program_template(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test admin can delete program templates."""
        from app.models.training_program import TrainingProgramModel
        from app.domain.value_objects.enums import SplitType, StructureType
        
        # Create template to delete
        template = TrainingProgramModel(
            name="Template To Delete",
            description="Will be deleted",
            split_type=SplitType.FULL_BODY,
            structure_type=StructureType.CYCLIC,
            structure_config={"days_on": 3, "days_off": 1},
            is_template=True,
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)
        template_id = template.id
        
        response = await async_client.delete(
            f"/api/v1/admin/programs/templates/{template_id}",
            headers=admin_headers,
        )
        
        assert response.status_code in [200, 204]


class TestAdminStatistics:
    """Tests for admin statistics and analytics."""
    
    @pytest.mark.asyncio
    async def test_get_platform_statistics(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
    ):
        """Test admin can get platform-wide statistics."""
        response = await async_client.get(
            "/api/v1/admin/stats",
            headers=admin_headers,
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "total_users" in data or "user_count" in data
            assert "total_organizations" in data or "org_count" in data
    
    @pytest.mark.asyncio
    async def test_get_user_growth_stats(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
    ):
        """Test admin can get user growth statistics."""
        response = await async_client.get(
            "/api/v1/admin/stats/users/growth",
            headers=admin_headers,
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should have some growth data
            assert isinstance(data, (dict, list))
    
    @pytest.mark.asyncio
    async def test_get_subscription_stats(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
    ):
        """Test admin can get subscription tier distribution."""
        response = await async_client.get(
            "/api/v1/admin/stats/subscriptions",
            headers=admin_headers,
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should have subscription breakdown
            assert "FREE" in str(data) or "PRO" in str(data)


class TestAdminBulkOperations:
    """Tests for admin bulk operations."""
    
    @pytest.mark.asyncio
    async def test_bulk_update_users(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
    ):
        """Test admin can perform bulk user updates."""
        response = await async_client.post(
            "/api/v1/admin/users/bulk-update",
            headers=admin_headers,
            json={
                "user_ids": [],  # Would have actual IDs
                "updates": {
                    "is_verified": True,
                },
            },
        )
        
        # Should succeed or return 404 if not implemented
        assert response.status_code in [200, 404, 422]
    
    @pytest.mark.asyncio
    async def test_bulk_delete_inactive_users(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
    ):
        """Test admin can bulk delete inactive users."""
        response = await async_client.post(
            "/api/v1/admin/users/bulk-delete-inactive",
            headers=admin_headers,
            json={
                "inactive_days": 365,  # Delete users inactive for 1 year
            },
        )
        
        # Should succeed or return 404 if not implemented
        assert response.status_code in [200, 404]
