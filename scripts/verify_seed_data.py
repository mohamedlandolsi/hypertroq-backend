"""
Verify that seed data has been successfully inserted into the database.

This script checks:
1. Admin user exists
2. Default organization exists
3. 30 global exercises are present
4. 3 program templates with their sessions exist

Usage:
    python scripts/verify_seed_data.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.models.user import UserModel
from app.models.organization import OrganizationModel
from app.models.exercise import ExerciseModel
from app.models.training_program import TrainingProgramModel, WorkoutSessionModel


async def verify_seed_data():
    """Verify that seed data exists in the database."""
    
    # Create database connection
    database_url = str(settings.DIRECT_URL or settings.DATABASE_URL)
    engine = create_async_engine(database_url, echo=False)
    
    print("\n🔍 Verifying seed data...\n")
    
    async with AsyncSession(engine) as session:
        # 1. Check default organization
        org_query = select(OrganizationModel).where(OrganizationModel.name == "Default Organization")
        org_result = await session.execute(org_query)
        org = org_result.scalar_one_or_none()
        
        if org:
            print(f"✅ Default organization exists (ID: {org.id})")
            print(f"   Tier: {org.subscription_tier}, Status: {org.subscription_status}")
        else:
            print("❌ Default organization NOT FOUND")
            return False
        
        # 2. Check admin user
        admin_query = select(UserModel).where(UserModel.email == "admin@hypertroq.com")
        admin_result = await session.execute(admin_query)
        admin = admin_result.scalar_one_or_none()
        
        if admin:
            print(f"✅ Admin user exists (ID: {admin.id})")
            print(f"   Name: {admin.full_name}, Role: {admin.role}, Active: {admin.is_active}")
        else:
            print("❌ Admin user NOT FOUND")
            return False
        
        # 3. Check global exercises
        exercises_query = select(func.count()).select_from(ExerciseModel).where(ExerciseModel.is_global == True)
        exercises_result = await session.execute(exercises_query)
        exercise_count = exercises_result.scalar()
        
        if exercise_count == 30:
            print(f"✅ Found {exercise_count} global exercises")
            
            # Count by equipment type
            equipment_query = select(
                ExerciseModel.equipment,
                func.count(ExerciseModel.id).label('count')
            ).where(
                ExerciseModel.is_global == True
            ).group_by(ExerciseModel.equipment)
            
            equipment_result = await session.execute(equipment_query)
            equipment_counts = equipment_result.all()
            
            print("   Equipment breakdown:")
            for equipment, count in equipment_counts:
                print(f"   - {equipment}: {count} exercises")
        else:
            print(f"❌ Expected 30 global exercises, found {exercise_count}")
            return False
        
        # 4. Check program templates
        templates_query = select(TrainingProgramModel).where(TrainingProgramModel.is_template == True)
        templates_result = await session.execute(templates_query)
        templates = templates_result.scalars().all()
        
        if len(templates) == 3:
            print(f"✅ Found {len(templates)} program templates:")
            
            for template in templates:
                # Count sessions for this template
                sessions_query = select(func.count()).select_from(WorkoutSessionModel).where(
                    WorkoutSessionModel.program_id == template.id
                )
                sessions_result = await session.execute(sessions_query)
                session_count = sessions_result.scalar()
                
                print(f"   - {template.name} ({template.split_type})")
                print(f"     Structure: {template.structure_type}, Sessions: {session_count}")
        else:
            print(f"❌ Expected 3 program templates, found {len(templates)}")
            return False
        
        # 5. Check total workout sessions
        total_sessions_query = select(func.count()).select_from(WorkoutSessionModel)
        total_sessions_result = await session.execute(total_sessions_query)
        total_sessions = total_sessions_result.scalar()
        
        expected_sessions = 4 + 3 + 3  # Upper/Lower (4) + PPL (3) + Full Body (3)
        if total_sessions == expected_sessions:
            print(f"✅ Found {total_sessions} workout sessions (4 + 3 + 3)")
        else:
            print(f"❌ Expected {expected_sessions} workout sessions, found {total_sessions}")
            return False
    
    await engine.dispose()
    
    print("\n✅ All seed data verification passed!\n")
    print("📊 Summary:")
    print("   - 1 Default Organization")
    print("   - 1 Admin User")
    print("   - 30 Global Exercises")
    print("   - 3 Program Templates")
    print("   - 10 Workout Sessions\n")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(verify_seed_data())
    exit(0 if success else 1)
