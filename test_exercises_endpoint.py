"""Test script to debug exercises endpoint error."""
import asyncio
import sys
sys.path.insert(0, 'd:\\MyProject\\hypertroq\\hypertroq-backend')

async def test_exercises():
    from app.infrastructure.database.connection import db_manager
    from app.repositories.exercise_repository import ExerciseRepository
    from app.schemas.exercise import ExerciseFilter
    
    try:
        # Test database connection
        await db_manager.test_connection()
        print("✓ Database connection successful")
        
        # Get a session
        from app.infrastructure.database import get_db
        async for session in get_db():
            # Create repository
            repo = ExerciseRepository(session)
            
            # Try to list exercises
            filters = ExerciseFilter(
                search=None,
                equipment=None,
                muscle_group=None,
                is_global=None,
                skip=0,
                limit=20
            )
            
            # This is what the endpoint does
            from uuid import uuid4
            org_id = uuid4()  # Fake org ID for testing
            
            exercises, total = await repo.list_exercises(filters=filters, org_id=org_id)
            print(f"✓ Found {total} exercises")
            print(f"✓ Retrieved {len(exercises)} exercise entities")
            
            if exercises:
                first_exercise = exercises[0]
                print(f"✓ First exercise: {first_exercise.name}")
                print(f"✓ Exercise has organization_id: {first_exercise.organization_id}")
            else:
                print("! No exercises found in database - this is expected if no data seeded")
            
            break
            
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_exercises())
