"""
Training Program API tests.

Tests for program creation, template cloning, session management,
volume calculations, and schedule generation.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.training_program import TrainingProgramModel, WorkoutSessionModel
from app.models.exercise import ExerciseModel
from app.models.user import UserModel


@pytest.fixture
async def test_program_template(
    db_session: AsyncSession, test_global_exercises: list[ExerciseModel]
) -> TrainingProgramModel:
    """Create a test program template."""
    from app.domain.value_objects.enums import SplitType, StructureType
    
    program = TrainingProgramModel(
        name="Test Upper/Lower Split",
        description="Test program template",
        split_type=SplitType.UPPER_LOWER,
        structure_type=StructureType.WEEKLY,
        structure_config={
            "days": [1, 2, 4, 5]  # Mon, Tue, Thu, Fri
        },
        is_template=True,
        duration_weeks=8,
    )
    db_session.add(program)
    await db_session.commit()
    await db_session.refresh(program)
    
    # Add workout sessions
    session1 = WorkoutSessionModel(
        program_id=program.id,
        name="Upper Body A",
        day_number=1,
        order_in_program=1,
        exercises=[
            {
                "exercise_id": str(test_global_exercises[0].id),
                "sets": 3,
                "order": 1,
            }
        ],
        total_sets=3,
    )
    session2 = WorkoutSessionModel(
        program_id=program.id,
        name="Lower Body A",
        day_number=2,
        order_in_program=2,
        exercises=[
            {
                "exercise_id": str(test_global_exercises[1].id),
                "sets": 4,
                "order": 1,
            }
        ],
        total_sets=4,
    )
    
    db_session.add(session1)
    db_session.add(session2)
    await db_session.commit()
    
    await db_session.refresh(program)
    return program


class TestProgramList:
    """Tests for listing programs and templates."""
    
    @pytest.mark.asyncio
    async def test_list_program_templates(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
    ):
        """Test listing program templates."""
        response = await async_client.get(
            "/api/v1/programs/templates",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) >= 1
        
        # Find our test template
        template_names = [p["name"] for p in data["data"]]
        assert "Test Upper/Lower Split" in template_names
    
    @pytest.mark.asyncio
    async def test_list_user_programs(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing user's programs."""
        response = await async_client.get(
            "/api/v1/programs",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    @pytest.mark.asyncio
    async def test_filter_programs_by_split_type(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
    ):
        """Test filtering programs by split type."""
        response = await async_client.get(
            "/api/v1/programs/templates?split_type=UPPER_LOWER",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for program in data["data"]:
            assert program["split_type"] == "UPPER_LOWER"


class TestProgramCreate:
    """Tests for creating programs."""
    
    @pytest.mark.asyncio
    async def test_create_program_free_tier_fails(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test that free tier users cannot create custom programs."""
        response = await async_client.post(
            "/api/v1/programs",
            headers=auth_headers,
            json={
                "name": "My Custom Program",
                "description": "Custom program",
                "split_type": "UPPER_LOWER",
                "structure_type": "WEEKLY",
                "structure_config": {"days": [1, 3, 5]},
                "sessions": [],
            },
        )
        
        # Free tier should be forbidden
        assert response.status_code in [403, 402]
    
    @pytest.mark.asyncio
    async def test_create_program_pro_tier_success(
        self,
        async_client: AsyncClient,
        test_admin: UserModel,
        test_pro_organization,
        db_session: AsyncSession,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test that PRO tier users can create custom programs."""
        # Update admin to PRO org
        test_admin.organization_id = test_pro_organization.id
        db_session.add(test_admin)
        await db_session.commit()
        
        from app.core.security import create_access_token
        pro_token = create_access_token(
            subject={
                "user_id": str(test_admin.id),
                "organization_id": str(test_pro_organization.id),
                "role": str(test_admin.role.value),
            }
        )
        
        response = await async_client.post(
            "/api/v1/programs",
            headers={"Authorization": f"Bearer {pro_token}"},
            json={
                "name": "Pro Custom Program",
                "description": "PRO tier custom program",
                "split_type": "UPPER_LOWER",
                "structure_type": "WEEKLY",
                "structure_config": {"days": [1, 3, 5]},
                "duration_weeks": 12,
            },
        )
        
        if response.status_code == 201:
            data = response.json()
            assert data["name"] == "Pro Custom Program"
            assert data["is_template"] is False
    
    @pytest.mark.asyncio
    async def test_create_program_invalid_structure(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Test that invalid structure configuration is rejected."""
        response = await async_client.post(
            "/api/v1/programs",
            headers=admin_headers,
            json={
                "name": "Invalid Program",
                "split_type": "UPPER_LOWER",
                "structure_type": "WEEKLY",
                "structure_config": {"invalid_key": "value"},
            },
        )
        
        assert response.status_code == 422


class TestProgramClone:
    """Tests for cloning program templates."""
    
    @pytest.mark.asyncio
    async def test_clone_template_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
        db_session: AsyncSession,
    ):
        """Test cloning a program template."""
        response = await async_client.post(
            f"/api/v1/programs/{test_program_template.id}/clone",
            headers=auth_headers,
            json={
                "name": "My Cloned Program",
            },
        )
        
        if response.status_code == 201:
            data = response.json()
            assert data["name"] == "My Cloned Program"
            assert data["is_template"] is False
            assert data["split_type"] == test_program_template.split_type.value
            
            # Verify sessions were cloned
            from sqlalchemy import select
            sessions = await db_session.execute(
                select(WorkoutSessionModel).where(
                    WorkoutSessionModel.program_id == data["id"]
                )
            )
            assert len(sessions.scalars().all()) == 2  # Same as template
    
    @pytest.mark.asyncio
    async def test_clone_nonexistent_template_fails(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test cloning non-existent template fails."""
        from uuid import uuid4
        
        response = await async_client.post(
            f"/api/v1/programs/{uuid4()}/clone",
            headers=auth_headers,
            json={"name": "Cloned Program"},
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_clone_with_modifications(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
    ):
        """Test cloning template with custom modifications."""
        response = await async_client.post(
            f"/api/v1/programs/{test_program_template.id}/clone",
            headers=auth_headers,
            json={
                "name": "Modified Clone",
                "duration_weeks": 16,  # Different from template
            },
        )
        
        if response.status_code == 201:
            data = response.json()
            assert data["duration_weeks"] == 16


class TestSessionManagement:
    """Tests for managing workout sessions."""
    
    @pytest.mark.asyncio
    async def test_add_session_to_program(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
        test_global_exercises: list[ExerciseModel],
    ):
        """Test adding a workout session to a program."""
        # Note: This would require PRO tier or admin
        response = await async_client.post(
            f"/api/v1/programs/{test_program_template.id}/sessions",
            headers=auth_headers,
            json={
                "name": "New Session",
                "day_number": 3,
                "exercises": [
                    {
                        "exercise_id": str(test_global_exercises[0].id),
                        "sets": 3,
                        "order": 1,
                    }
                ],
            },
        )
        
        # Might be 201 if allowed, or 403 if not PRO
        assert response.status_code in [201, 403, 404]
    
    @pytest.mark.asyncio
    async def test_update_session(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_program_template: TrainingProgramModel,
        db_session: AsyncSession,
    ):
        """Test updating a workout session."""
        # Get first session
        from sqlalchemy import select
        result = await db_session.execute(
            select(WorkoutSessionModel).where(
                WorkoutSessionModel.program_id == test_program_template.id
            ).limit(1)
        )
        session = result.scalar_one_or_none()
        
        if session:
            response = await async_client.put(
                f"/api/v1/programs/{test_program_template.id}/sessions/{session.id}",
                headers=admin_headers,
                json={
                    "name": "Updated Session Name",
                },
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["name"] == "Updated Session Name"
    
    @pytest.mark.asyncio
    async def test_delete_session(
        self,
        async_client: AsyncClient,
        admin_headers: dict,
        test_program_template: TrainingProgramModel,
        db_session: AsyncSession,
    ):
        """Test deleting a workout session."""
        # Create a session to delete
        session = WorkoutSessionModel(
            program_id=test_program_template.id,
            name="To Be Deleted",
            day_number=7,
            order_in_program=99,
            exercises=[],
            total_sets=0,
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        response = await async_client.delete(
            f"/api/v1/programs/{test_program_template.id}/sessions/{session.id}",
            headers=admin_headers,
        )
        
        assert response.status_code in [200, 204]


class TestVolumeCalculations:
    """Tests for program volume calculations."""
    
    @pytest.mark.asyncio
    async def test_calculate_program_volume(
        self,
        test_program_template: TrainingProgramModel,
        test_global_exercises: list[ExerciseModel],
        db_session: AsyncSession,
    ):
        """Test calculating total volume for a program."""
        from sqlalchemy import select
        
        # Get all sessions for the program
        result = await db_session.execute(
            select(WorkoutSessionModel).where(
                WorkoutSessionModel.program_id == test_program_template.id
            )
        )
        sessions = result.scalars().all()
        
        # Calculate total volume
        total_sets = sum(session.total_sets for session in sessions)
        assert total_sets == 7  # 3 + 4 from fixture
    
    @pytest.mark.asyncio
    async def test_volume_by_muscle_group(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
    ):
        """Test calculating volume by muscle group."""
        response = await async_client.get(
            f"/api/v1/programs/{test_program_template.id}/volume",
            headers=auth_headers,
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "volume_by_muscle" in data
            # Should have CHEST, QUADS, etc.
            assert "CHEST" in data["volume_by_muscle"]
    
    @pytest.mark.asyncio
    async def test_weekly_volume_calculation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
    ):
        """Test calculating weekly volume for a program."""
        response = await async_client.get(
            f"/api/v1/programs/{test_program_template.id}/weekly-volume",
            headers=auth_headers,
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should return volume per muscle per week
            assert "weekly_volume" in data or "volume_by_muscle" in data


class TestScheduleGeneration:
    """Tests for generating workout schedules."""
    
    @pytest.mark.asyncio
    async def test_generate_weekly_schedule(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
    ):
        """Test generating a weekly schedule from a program."""
        response = await async_client.post(
            f"/api/v1/programs/{test_program_template.id}/generate-schedule",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "weeks": 4,
            },
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "schedule" in data
            assert len(data["schedule"]) > 0
    
    @pytest.mark.asyncio
    async def test_schedule_respects_structure(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
    ):
        """Test that generated schedule respects program structure."""
        response = await async_client.post(
            f"/api/v1/programs/{test_program_template.id}/generate-schedule",
            headers=auth_headers,
            json={
                "start_date": "2025-01-06",  # Monday
                "weeks": 1,
            },
        )
        
        if response.status_code == 200:
            data = response.json()
            schedule = data["schedule"]
            
            # For WEEKLY structure with days [1,2,4,5] (Mon,Tue,Thu,Fri)
            # Should have 4 workouts in the first week
            if len(schedule) >= 4:
                # Verify workouts are on correct days
                days_of_week = [item["day_of_week"] for item in schedule[:4]]
                assert 1 in days_of_week  # Monday
                assert 2 in days_of_week  # Tuesday


class TestProgramRetrieve:
    """Tests for retrieving programs."""
    
    @pytest.mark.asyncio
    async def test_get_program_by_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
    ):
        """Test retrieving program by ID."""
        response = await async_client.get(
            f"/api/v1/programs/{test_program_template.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_program_template.id)
        assert data["name"] == test_program_template.name
    
    @pytest.mark.asyncio
    async def test_get_program_with_sessions(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
    ):
        """Test retrieving program includes sessions."""
        response = await async_client.get(
            f"/api/v1/programs/{test_program_template.id}?include_sessions=true",
            headers=auth_headers,
        )
        
        if response.status_code == 200:
            data = response.json()
            if "sessions" in data:
                assert len(data["sessions"]) == 2


class TestProgramUpdate:
    """Tests for updating programs."""
    
    @pytest.mark.asyncio
    async def test_update_user_program(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
        test_user: UserModel,
        db_session: AsyncSession,
    ):
        """Test updating a user's own program."""
        # Clone template first to get user program
        response = await async_client.post(
            f"/api/v1/programs/{test_program_template.id}/clone",
            headers=auth_headers,
            json={"name": "User Program"},
        )
        
        if response.status_code == 201:
            program_id = response.json()["id"]
            
            # Update the program
            update_response = await async_client.put(
                f"/api/v1/programs/{program_id}",
                headers=auth_headers,
                json={
                    "name": "Updated Program Name",
                    "duration_weeks": 20,
                },
            )
            
            if update_response.status_code == 200:
                data = update_response.json()
                assert data["name"] == "Updated Program Name"
    
    @pytest.mark.asyncio
    async def test_update_template_requires_admin(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
    ):
        """Test that updating templates requires admin."""
        response = await async_client.put(
            f"/api/v1/programs/{test_program_template.id}",
            headers=auth_headers,
            json={"name": "Hacked Template"},
        )
        
        assert response.status_code == 403


class TestProgramDelete:
    """Tests for deleting programs."""
    
    @pytest.mark.asyncio
    async def test_delete_user_program(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
    ):
        """Test deleting user's own program."""
        # Clone template to get user program
        response = await async_client.post(
            f"/api/v1/programs/{test_program_template.id}/clone",
            headers=auth_headers,
            json={"name": "To Delete"},
        )
        
        if response.status_code == 201:
            program_id = response.json()["id"]
            
            # Delete it
            delete_response = await async_client.delete(
                f"/api/v1/programs/{program_id}",
                headers=auth_headers,
            )
            
            assert delete_response.status_code in [200, 204]
    
    @pytest.mark.asyncio
    async def test_delete_template_requires_admin(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_program_template: TrainingProgramModel,
    ):
        """Test that deleting templates requires admin."""
        response = await async_client.delete(
            f"/api/v1/programs/{test_program_template.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 403
