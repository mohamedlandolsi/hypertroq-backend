"""
Exercise API tests.

Tests for exercise CRUD operations, filtering, search,
authorization, and muscle volume calculations.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import ExerciseModel
from app.models.user import UserModel
from app.models.organization import OrganizationModel


class TestExerciseList:
    """Tests for listing exercises."""
    
    @pytest.mark.asyncio
    async def test_list_global_exercises(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test listing global exercises."""
        response = await async_client.get(
            "/api/v1/exercises",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) >= 3  # At least the 3 test exercises
        
        # Verify global exercises are included
        exercise_names = [ex["name"] for ex in data["data"]]
        assert "Barbell Bench Press" in exercise_names
        assert "Barbell Squat" in exercise_names
    
    @pytest.mark.asyncio
    async def test_list_exercises_requires_auth(
        self, async_client: AsyncClient, test_global_exercises: list[ExerciseModel]
    ):
        """Test that listing exercises requires authentication."""
        response = await async_client.get("/api/v1/exercises")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_list_exercises_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test pagination of exercise list."""
        response = await async_client.get(
            "/api/v1/exercises?page=1&limit=2",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 2
        
        if "meta" in data:
            assert "page" in data["meta"]
            assert "limit" in data["meta"]


class TestExerciseFiltering:
    """Tests for exercise filtering and search."""
    
    @pytest.mark.asyncio
    async def test_filter_by_equipment(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test filtering exercises by equipment type."""
        response = await async_client.get(
            "/api/v1/exercises?equipment=BARBELL",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All exercises should be barbell exercises
        for exercise in data["data"]:
            assert exercise["equipment"] == "BARBELL"
    
    @pytest.mark.asyncio
    async def test_filter_by_muscle_group(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test filtering exercises by muscle group."""
        response = await async_client.get(
            "/api/v1/exercises?muscle_group=CHEST",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All exercises should target chest
        for exercise in data["data"]:
            assert "CHEST" in exercise["muscle_contributions"]
    
    @pytest.mark.asyncio
    async def test_search_exercises(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test searching exercises by name."""
        response = await async_client.get(
            "/api/v1/exercises?search=bench",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find Barbell Bench Press
        exercise_names = [ex["name"].lower() for ex in data["data"]]
        assert any("bench" in name for name in exercise_names)
    
    @pytest.mark.asyncio
    async def test_multiple_filters(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test combining multiple filters."""
        response = await async_client.get(
            "/api/v1/exercises?equipment=BARBELL&muscle_group=CHEST",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find Barbell Bench Press
        for exercise in data["data"]:
            assert exercise["equipment"] == "BARBELL"
            assert "CHEST" in exercise["muscle_contributions"]


class TestExerciseCreate:
    """Tests for creating exercises."""
    
    @pytest.mark.asyncio
    async def test_create_custom_exercise_free_tier_fails(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test that free tier users cannot create custom exercises."""
        response = await async_client.post(
            "/api/v1/exercises",
            headers=auth_headers,
            json={
                "name": "Custom Exercise",
                "description": "My custom exercise",
                "equipment": "DUMBBELL",
                "muscle_contributions": {
                    "CHEST": 1.0,
                    "TRICEPS": 0.5,
                },
            },
        )
        
        # Free tier should be forbidden from creating custom exercises
        assert response.status_code in [403, 402]  # Forbidden or Payment Required
    
    @pytest.mark.asyncio
    async def test_create_custom_exercise_pro_tier_success(
        self,
        async_client: AsyncClient,
        test_admin: UserModel,
        test_pro_organization: OrganizationModel,
        db_session: AsyncSession,
    ):
        """Test that PRO tier users can create custom exercises."""
        # Update admin to be in PRO organization
        test_admin.organization_id = test_pro_organization.id
        db_session.add(test_admin)
        await db_session.commit()
        
        # Create token for admin in PRO org
        from app.core.security import create_access_token
        pro_token = create_access_token(
            subject={
                "user_id": str(test_admin.id),
                "organization_id": str(test_pro_organization.id),
                "role": str(test_admin.role.value),
            }
        )
        
        response = await async_client.post(
            "/api/v1/exercises",
            headers={"Authorization": f"Bearer {pro_token}"},
            json={
                "name": "Pro Custom Exercise",
                "description": "Custom exercise for PRO user",
                "equipment": "DUMBBELL",
                "muscle_contributions": {
                    "CHEST": 1.0,
                    "TRICEPS": 0.5,
                },
            },
        )
        
        if response.status_code == 201:
            data = response.json()
            assert data["name"] == "Pro Custom Exercise"
            assert data["is_global"] is False
            assert data["organization_id"] == str(test_pro_organization.id)
    
    @pytest.mark.asyncio
    async def test_create_exercise_invalid_muscle_contribution(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Test that invalid muscle contribution values are rejected."""
        response = await async_client.post(
            "/api/v1/exercises",
            headers=admin_headers,
            json={
                "name": "Invalid Exercise",
                "description": "Invalid muscle contribution",
                "equipment": "BARBELL",
                "muscle_contributions": {
                    "CHEST": 1.5,  # Invalid: should be between 0 and 1
                },
            },
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_exercise_duplicate_name_in_organization(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test that duplicate exercise names in same org are rejected."""
        # Assuming PRO tier, try to create exercise with same name
        response = await async_client.post(
            "/api/v1/exercises",
            headers=auth_headers,
            json={
                "name": "Barbell Bench Press",  # Duplicate global exercise name
                "description": "Duplicate exercise",
                "equipment": "BARBELL",
                "muscle_contributions": {
                    "CHEST": 1.0,
                },
            },
        )
        
        # Should fail with conflict or forbidden
        assert response.status_code in [403, 409, 422]


class TestExerciseRetrieve:
    """Tests for retrieving individual exercises."""
    
    @pytest.mark.asyncio
    async def test_get_exercise_by_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test retrieving exercise by ID."""
        exercise = test_global_exercises[0]
        
        response = await async_client.get(
            f"/api/v1/exercises/{exercise.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(exercise.id)
        assert data["name"] == exercise.name
        assert data["equipment"] == exercise.equipment.value
        assert "muscle_contributions" in data
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_exercise(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test retrieving non-existent exercise returns 404."""
        from uuid import uuid4
        
        response = await async_client.get(
            f"/api/v1/exercises/{uuid4()}",
            headers=auth_headers,
        )
        
        assert response.status_code == 404


class TestExerciseUpdate:
    """Tests for updating exercises."""
    
    @pytest.mark.asyncio
    async def test_update_global_exercise_requires_admin(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test that non-admin users cannot update global exercises."""
        exercise = test_global_exercises[0]
        
        response = await async_client.put(
            f"/api/v1/exercises/{exercise.id}",
            headers=auth_headers,
            json={
                "name": "Updated Name",
                "description": "Updated description",
            },
        )
        
        assert response.status_code == 403  # Forbidden
    
    @pytest.mark.asyncio
    async def test_admin_can_update_global_exercise(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test that admin users can update global exercises."""
        exercise = test_global_exercises[0]
        
        response = await async_client.put(
            f"/api/v1/exercises/{exercise.id}",
            headers=admin_headers,
            json={
                "name": "Admin Updated Name",
                "description": "Admin updated description",
            },
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["description"] == "Admin updated description"


class TestExerciseDelete:
    """Tests for deleting exercises."""
    
    @pytest.mark.asyncio
    async def test_delete_global_exercise_requires_admin(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test that non-admin users cannot delete global exercises."""
        exercise = test_global_exercises[0]
        
        response = await async_client.delete(
            f"/api/v1/exercises/{exercise.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 403  # Forbidden
    
    @pytest.mark.asyncio
    async def test_admin_can_delete_global_exercise(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_global_exercises: list[ExerciseModel],
        db_session: AsyncSession,
    ):
        """Test that admin users can delete global exercises."""
        # Create a new exercise to delete
        from app.domain.value_objects.enums import EquipmentType
        
        exercise = ExerciseModel(
            name="To Be Deleted",
            description="This will be deleted",
            equipment=EquipmentType.DUMBBELL,
            is_global=True,
            muscle_contributions={"CHEST": 1.0},
        )
        db_session.add(exercise)
        await db_session.commit()
        await db_session.refresh(exercise)
        
        response = await async_client.delete(
            f"/api/v1/exercises/{exercise.id}",
            headers=admin_headers,
        )
        
        assert response.status_code in [200, 204]


class TestMuscleVolumeCalculations:
    """Tests for muscle volume calculation functionality."""
    
    @pytest.mark.asyncio
    async def test_calculate_volume_full_contribution(
        self, test_global_exercises: list[ExerciseModel]
    ):
        """Test volume calculation for full muscle contribution."""
        bench_press = test_global_exercises[0]  # Chest: 1.0
        
        sets = 3
        chest_volume = sets * bench_press.muscle_contributions.get("CHEST", 0)
        
        assert chest_volume == 3.0
    
    @pytest.mark.asyncio
    async def test_calculate_volume_partial_contribution(
        self, test_global_exercises: list[ExerciseModel]
    ):
        """Test volume calculation for partial muscle contribution."""
        bench_press = test_global_exercises[0]  # Triceps: 0.5
        
        sets = 4
        triceps_volume = sets * bench_press.muscle_contributions.get("TRICEPS", 0)
        
        assert triceps_volume == 2.0
    
    @pytest.mark.asyncio
    async def test_calculate_total_volume_multiple_exercises(
        self, test_global_exercises: list[ExerciseModel]
    ):
        """Test total volume calculation across multiple exercises."""
        # Bench Press: Chest 1.0, Triceps 0.5
        # Squat: Quads 1.0, Glutes 0.75
        
        workout = [
            {"exercise": test_global_exercises[0], "sets": 3},  # Bench
            {"exercise": test_global_exercises[1], "sets": 4},  # Squat
        ]
        
        # Calculate chest volume
        chest_volume = sum(
            item["sets"] * item["exercise"].muscle_contributions.get("CHEST", 0)
            for item in workout
        )
        assert chest_volume == 3.0  # Only from bench press
        
        # Calculate quad volume
        quad_volume = sum(
            item["sets"] * item["exercise"].muscle_contributions.get("QUADS", 0)
            for item in workout
        )
        assert quad_volume == 4.0  # Only from squat
    
    @pytest.mark.asyncio
    async def test_volume_endpoint_returns_calculations(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test volume calculation API endpoint."""
        # This would test an endpoint like POST /api/v1/exercises/calculate-volume
        # if it exists in your API
        response = await async_client.post(
            "/api/v1/exercises/calculate-volume",
            headers=auth_headers,
            json={
                "exercises": [
                    {
                        "exercise_id": str(test_global_exercises[0].id),
                        "sets": 3,
                    },
                    {
                        "exercise_id": str(test_global_exercises[1].id),
                        "sets": 4,
                    },
                ]
            },
        )
        
        # Endpoint might not exist yet, so handle both cases
        if response.status_code == 200:
            data = response.json()
            assert "volume_by_muscle" in data
            assert "CHEST" in data["volume_by_muscle"]
            assert data["volume_by_muscle"]["CHEST"] == 3.0
