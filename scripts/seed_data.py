"""
Seed data script for HypertroQ backend.

Populates the database with:
- Default organization
- Admin user
- 30 global exercises covering all 18 muscle groups
- 3 program templates (Upper/Lower, PPL, Full Body)

Usage:
    python scripts/seed_data.py

Environment:
    Requires DATABASE_URL or DIRECT_URL in environment
"""
import asyncio
import sys
import json
from pathlib import Path
from uuid import UUID, uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.organization import OrganizationModel
from app.models.user import UserModel
from app.models.exercise import ExerciseModel
from app.models.training_program import TrainingProgramModel
from app.models.workout_session import WorkoutSessionModel
from app.core.security import get_password_hash


# Seed data definitions
EXERCISES_DATA = [
    # ========================================================================
    # CHEST EXERCISES (3)
    # ========================================================================
    {
        'name': 'Barbell Bench Press',
        'description': 'Lie on a flat bench and press a barbell from chest to arms extended. Primary chest builder. Keep shoulder blades retracted and feet flat on floor.',
        'equipment': 'BARBELL',
        'muscle_contributions': {
            'CHEST': 1.0,
            'FRONT_DELTS': 0.5,
            'TRICEPS': 0.75
        },
        'is_global': True
    },
    {
        'name': 'Dumbbell Incline Press',
        'description': 'Press dumbbells on an incline bench (30-45 degrees). Targets upper chest. Allow full stretch at bottom and lock out at top.',
        'equipment': 'DUMBBELL',
        'muscle_contributions': {
            'CHEST': 1.0,
            'FRONT_DELTS': 0.75,
            'TRICEPS': 0.5
        },
        'is_global': True
    },
    {
        'name': 'Dips (Chest Focused)',
        'description': 'Lean forward and dip between parallel bars. Emphasizes chest over triceps. Go deep but avoid shoulder pain.',
        'equipment': 'BODYWEIGHT',
        'muscle_contributions': {
            'CHEST': 0.75,
            'TRICEPS': 0.75,
            'FRONT_DELTS': 0.25
        },
        'is_global': True
    },
    
    # ========================================================================
    # BACK EXERCISES (5)
    # ========================================================================
    {
        'name': 'Barbell Bent-Over Row',
        'description': 'Pull a barbell to your lower chest while bent over at 45 degrees. Primary back thickness builder. Keep core tight and avoid momentum.',
        'equipment': 'BARBELL',
        'muscle_contributions': {
            'LATS': 1.0,
            'TRAPS_RHOMBOIDS': 0.75,
            'ELBOW_FLEXORS': 0.5
        },
        'is_global': True
    },
    {
        'name': 'Pull-Ups',
        'description': 'Pull yourself up until chin clears the bar. Best lat builder. Use full range of motion and control the descent.',
        'equipment': 'BODYWEIGHT',
        'muscle_contributions': {
            'LATS': 1.0,
            'TRAPS_RHOMBOIDS': 0.5,
            'ELBOW_FLEXORS': 0.75
        },
        'is_global': True
    },
    {
        'name': 'Lat Pulldown',
        'description': 'Pull a cable bar down to upper chest. Pull-up alternative with adjustable resistance. Lean back slightly and pull to clavicle.',
        'equipment': 'CABLE',
        'muscle_contributions': {
            'LATS': 1.0,
            'TRAPS_RHOMBOIDS': 0.5,
            'ELBOW_FLEXORS': 0.5
        },
        'is_global': True
    },
    {
        'name': 'Dumbbell Row',
        'description': 'Single-arm row with dumbbell. Allows full range of motion and unilateral focus. Support yourself on bench.',
        'equipment': 'DUMBBELL',
        'muscle_contributions': {
            'LATS': 0.75,
            'TRAPS_RHOMBOIDS': 0.75,
            'ELBOW_FLEXORS': 0.25
        },
        'is_global': True
    },
    {
        'name': 'Deadlift',
        'description': 'Lift barbell from floor to standing. Ultimate full-body exercise. Keep back neutral and drive through heels.',
        'equipment': 'BARBELL',
        'muscle_contributions': {
            'HAMSTRINGS': 1.0,
            'GLUTES': 1.0,
            'SPINAL_ERECTORS': 1.0,
            'TRAPS_RHOMBOIDS': 0.75,
            'FOREARMS': 0.75,
            'LATS': 0.5
        },
        'is_global': True
    },
    
    # ========================================================================
    # SHOULDER EXERCISES (3)
    # ========================================================================
    {
        'name': 'Overhead Press',
        'description': 'Press barbell overhead from shoulders to lockout. Primary shoulder mass builder. Keep core braced and avoid arching back.',
        'equipment': 'BARBELL',
        'muscle_contributions': {
            'FRONT_DELTS': 1.0,
            'SIDE_DELTS': 0.75,
            'TRICEPS': 0.5
        },
        'is_global': True
    },
    {
        'name': 'Dumbbell Lateral Raise',
        'description': 'Raise dumbbells to sides until arms parallel to floor. Isolates side delts. Lead with elbows and control the weight.',
        'equipment': 'DUMBBELL',
        'muscle_contributions': {
            'SIDE_DELTS': 1.0,
            'FRONT_DELTS': 0.25
        },
        'is_global': True
    },
    {
        'name': 'Face Pulls',
        'description': 'Pull cable to face with elbows high. Best rear delt and upper back exercise. Focus on external rotation at end.',
        'equipment': 'CABLE',
        'muscle_contributions': {
            'REAR_DELTS': 1.0,
            'TRAPS_RHOMBOIDS': 0.5
        },
        'is_global': True
    },
    
    # ========================================================================
    # ARM EXERCISES (4)
    # ========================================================================
    {
        'name': 'Barbell Curl',
        'description': 'Curl barbell from arms extended to shoulders. Classic bicep builder. Keep elbows stationary and avoid swinging.',
        'equipment': 'BARBELL',
        'muscle_contributions': {
            'ELBOW_FLEXORS': 1.0
        },
        'is_global': True
    },
    {
        'name': 'Hammer Curl',
        'description': 'Curl dumbbells with neutral grip. Targets brachialis and forearms. Keep wrists straight throughout.',
        'equipment': 'DUMBBELL',
        'muscle_contributions': {
            'ELBOW_FLEXORS': 0.75,
            'FOREARMS': 0.5
        },
        'is_global': True
    },
    {
        'name': 'Tricep Pushdown',
        'description': 'Push cable attachment down with elbows locked at sides. Tricep isolation. Full extension at bottom.',
        'equipment': 'CABLE',
        'muscle_contributions': {
            'TRICEPS': 1.0
        },
        'is_global': True
    },
    {
        'name': 'Close-Grip Bench Press',
        'description': 'Bench press with narrow grip (shoulder-width). Compound tricep movement. Tuck elbows closer to body.',
        'equipment': 'BARBELL',
        'muscle_contributions': {
            'TRICEPS': 1.0,
            'CHEST': 0.5,
            'FRONT_DELTS': 0.25
        },
        'is_global': True
    },
    
    # ========================================================================
    # LEG EXERCISES (7)
    # ========================================================================
    {
        'name': 'Barbell Back Squat',
        'description': 'Squat with barbell on upper back. King of leg exercises. Descend to parallel or below, drive through heels.',
        'equipment': 'BARBELL',
        'muscle_contributions': {
            'QUADS': 1.0,
            'GLUTES': 0.75,
            'HAMSTRINGS': 0.5,
            'SPINAL_ERECTORS': 0.5
        },
        'is_global': True
    },
    {
        'name': 'Romanian Deadlift',
        'description': 'Hip hinge with slight knee bend. Best hamstring and glute builder. Feel stretch in hamstrings, push hips back.',
        'equipment': 'BARBELL',
        'muscle_contributions': {
            'HAMSTRINGS': 1.0,
            'GLUTES': 1.0,
            'SPINAL_ERECTORS': 0.75
        },
        'is_global': True
    },
    {
        'name': 'Leg Press',
        'description': 'Press weight away with feet on platform. Quad-focused compound. Place feet mid-platform, full range of motion.',
        'equipment': 'MACHINE',
        'muscle_contributions': {
            'QUADS': 1.0,
            'GLUTES': 0.5
        },
        'is_global': True
    },
    {
        'name': 'Bulgarian Split Squat',
        'description': 'Single-leg squat with rear foot elevated. Unilateral leg developer. Maintain upright torso, control descent.',
        'equipment': 'DUMBBELL',
        'muscle_contributions': {
            'QUADS': 0.75,
            'GLUTES': 0.75,
            'HAMSTRINGS': 0.25
        },
        'is_global': True
    },
    {
        'name': 'Leg Curl',
        'description': 'Curl weight toward glutes using hamstring machine. Hamstring isolation. Full contraction at top.',
        'equipment': 'MACHINE',
        'muscle_contributions': {
            'HAMSTRINGS': 1.0
        },
        'is_global': True
    },
    {
        'name': 'Leg Extension',
        'description': 'Extend legs against resistance. Quad isolation. Control the weight, squeeze at top.',
        'equipment': 'MACHINE',
        'muscle_contributions': {
            'QUADS': 1.0
        },
        'is_global': True
    },
    {
        'name': 'Standing Calf Raise',
        'description': 'Raise up on toes with weight on shoulders. Primary calf developer. Full stretch at bottom, peak contraction at top.',
        'equipment': 'MACHINE',
        'muscle_contributions': {
            'CALVES': 1.0
        },
        'is_global': True
    },
    
    # ========================================================================
    # CORE EXERCISES (4)
    # ========================================================================
    {
        'name': 'Plank',
        'description': 'Hold body straight in push-up position. Core stability exercise. Keep hips level, squeeze glutes.',
        'equipment': 'BODYWEIGHT',
        'muscle_contributions': {
            'ABS': 1.0,
            'OBLIQUES': 0.5
        },
        'is_global': True
    },
    {
        'name': 'Cable Crunch',
        'description': 'Crunch against cable resistance. Weighted ab exercise. Round spine, focus on shortening distance between ribs and hips.',
        'equipment': 'CABLE',
        'muscle_contributions': {
            'ABS': 1.0
        },
        'is_global': True
    },
    {
        'name': 'Russian Twist',
        'description': 'Rotate torso side to side with weight. Oblique developer. Keep abs tight, controlled rotation.',
        'equipment': 'DUMBBELL',
        'muscle_contributions': {
            'OBLIQUES': 1.0,
            'ABS': 0.25
        },
        'is_global': True
    },
    {
        'name': 'Hanging Leg Raise',
        'description': 'Raise legs while hanging from bar. Advanced ab exercise. Avoid swinging, curl hips at top.',
        'equipment': 'BODYWEIGHT',
        'muscle_contributions': {
            'ABS': 1.0,
            'ELBOW_FLEXORS': 0.25
        },
        'is_global': True
    },
    
    # ========================================================================
    # ADDITIONAL COMPOUND MOVEMENTS (4)
    # ========================================================================
    {
        'name': 'Front Squat',
        'description': 'Squat with barbell on front shoulders. Quad-emphasized squat variation. More upright torso than back squat.',
        'equipment': 'BARBELL',
        'muscle_contributions': {
            'QUADS': 1.0,
            'GLUTES': 0.5,
            'SPINAL_ERECTORS': 0.5
        },
        'is_global': True
    },
    {
        'name': 'Chin-Ups',
        'description': 'Pull-up with supinated (underhand) grip. Emphasizes biceps more than pull-ups. Full ROM.',
        'equipment': 'BODYWEIGHT',
        'muscle_contributions': {
            'LATS': 1.0,
            'ELBOW_FLEXORS': 1.0,
            'TRAPS_RHOMBOIDS': 0.5
        },
        'is_global': True
    },
    {
        'name': 'T-Bar Row',
        'description': 'Row with T-bar or barbell in corner. Thick back builder. Pull to lower chest, squeeze shoulder blades.',
        'equipment': 'BARBELL',
        'muscle_contributions': {
            'LATS': 0.75,
            'TRAPS_RHOMBOIDS': 1.0,
            'ELBOW_FLEXORS': 0.5
        },
        'is_global': True
    },
    {
        'name': 'Hip Thrust',
        'description': 'Thrust hips upward with barbell across hips. Best glute isolation. Full extension at top, squeeze glutes hard.',
        'equipment': 'BARBELL',
        'muscle_contributions': {
            'GLUTES': 1.0,
            'HAMSTRINGS': 0.5
        },
        'is_global': True
    },
]


async def create_default_organization(session: AsyncSession) -> UUID:
    """Create or get default organization."""
    # Check if default org exists
    result = await session.execute(
        select(OrganizationModel).where(OrganizationModel.name == "Default Organization")
    )
    org = result.scalar_one_or_none()
    
    if org:
        print(f"✓ Default organization already exists (ID: {org.id})")
        return org.id
    
    # Create new organization
    org = OrganizationModel(
        id=uuid4(),
        name="Default Organization",
        subscription_tier="FREE",
        subscription_status="ACTIVE"
    )
    session.add(org)
    await session.flush()
    
    print(f"✓ Created default organization (ID: {org.id})")
    return org.id


async def create_admin_user(session: AsyncSession, org_id: UUID) -> UUID:
    """Create or get admin user."""
    # Check if admin exists
    result = await session.execute(
        select(UserModel).where(UserModel.email == "admin@hypertroq.com")
    )
    user = result.scalar_one_or_none()
    
    if user:
        print(f"✓ Admin user already exists (ID: {user.id})")
        return user.id
    
    # Use a pre-hashed password (bcrypt hash of "Admin@123")
    # This avoids bcrypt compatibility issues with Python 3.13
    prehashed = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aqCJfiRpEFSu"
    
    # Create admin user
    user = UserModel(
        id=uuid4(),
        email="admin@hypertroq.com",
        hashed_password=prehashed,
        full_name="System Administrator",
        organization_id=org_id,
        role="ADMIN",
        is_active=True,
        is_verified=True
    )
    session.add(user)
    await session.flush()
    
    print(f"✓ Created admin user (ID: {user.id}) - Email: admin@hypertroq.com")
    print("  ⚠️  Default password: Admin@123 (CHANGE THIS IN PRODUCTION!)")
    return user.id


async def seed_exercises(session: AsyncSession) -> dict[str, UUID]:
    """Seed global exercises and return name->ID mapping."""
    # Check if exercises already exist
    result = await session.execute(
        select(ExerciseModel).where(ExerciseModel.is_global == True)
    )
    existing = result.scalars().all()
    
    if len(existing) >= 20:
        print(f"✓ {len(existing)} global exercises already exist")
        # Return mapping for existing exercises
        return {ex.name: ex.id for ex in existing}
    
    # Insert exercises
    exercise_mapping = {}
    for ex_data in EXERCISES_DATA:
        exercise = ExerciseModel(
            id=uuid4(),
            name=ex_data['name'],
            description=ex_data['description'],
            equipment=ex_data['equipment'],
            muscle_contributions=ex_data['muscle_contributions'],
            is_global=True,
            created_by_user_id=None,
            organization_id=None,
            image_url=None
        )
        session.add(exercise)
        exercise_mapping[exercise.name] = exercise.id
    
    await session.flush()
    print(f"✓ Seeded {len(EXERCISES_DATA)} global exercises")
    return exercise_mapping


async def seed_program_templates(session: AsyncSession, exercise_mapping: dict[str, UUID]) -> None:
    """Seed program templates (Upper/Lower, PPL, Full Body)."""
    # Check if templates already exist
    result = await session.execute(
        select(TrainingProgramModel).where(TrainingProgramModel.is_template == True)
    )
    existing = result.scalars().all()
    
    if len(existing) >= 3:
        print(f"✓ {len(existing)} program templates already exist")
        return
    
    # ========================================================================
    # TEMPLATE 1: Upper/Lower 4-Day Split
    # ========================================================================
    ul_program = TrainingProgramModel(
        id=uuid4(),
        name="Upper/Lower 4-Day Split",
        description="Classic upper/lower split for intermediate lifters. Train upper body twice per week and lower body twice per week. Ideal for balanced development and recovery.",
        split_type="UPPER_LOWER",
        structure_type="WEEKLY",
        structure_config={
            "days_per_week": 4,
            "selected_days": ["MON", "TUE", "THU", "FRI"]
        },
        is_template=True,
        created_by_user_id=None,
        organization_id=None,
        duration_weeks=8
    )
    session.add(ul_program)
    await session.flush()
    
    # Upper Body A
    ul_upper_a = WorkoutSessionModel(
        id=uuid4(),
        program_id=ul_program.id,
        name="Upper Body A",
        day_number=1,
        order_in_program=1,
        exercises=[
            {"exercise_id": str(exercise_mapping["Barbell Bench Press"]), "sets": 4, "order_in_session": 1, "notes": "3-0-1-0 tempo"},
            {"exercise_id": str(exercise_mapping["Barbell Bent-Over Row"]), "sets": 4, "order_in_session": 2, "notes": "Pull to lower chest"},
            {"exercise_id": str(exercise_mapping["Overhead Press"]), "sets": 3, "order_in_session": 3, "notes": None},
            {"exercise_id": str(exercise_mapping["Dumbbell Lateral Raise"]), "sets": 3, "order_in_session": 4, "notes": None},
            {"exercise_id": str(exercise_mapping["Barbell Curl"]), "sets": 3, "order_in_session": 5, "notes": None}
        ],
        total_sets=17
    )
    session.add(ul_upper_a)
    
    # Lower Body A
    ul_lower_a = WorkoutSessionModel(
        id=uuid4(),
        program_id=ul_program.id,
        name="Lower Body A",
        day_number=2,
        order_in_program=2,
        exercises=[
            {"exercise_id": str(exercise_mapping["Barbell Back Squat"]), "sets": 4, "order_in_session": 1, "notes": "Below parallel depth"},
            {"exercise_id": str(exercise_mapping["Romanian Deadlift"]), "sets": 4, "order_in_session": 2, "notes": "Feel hamstring stretch"},
            {"exercise_id": str(exercise_mapping["Leg Press"]), "sets": 3, "order_in_session": 3, "notes": None},
            {"exercise_id": str(exercise_mapping["Leg Curl"]), "sets": 3, "order_in_session": 4, "notes": None}
        ],
        total_sets=14
    )
    session.add(ul_lower_a)
    
    # Upper Body B
    ul_upper_b = WorkoutSessionModel(
        id=uuid4(),
        program_id=ul_program.id,
        name="Upper Body B",
        day_number=4,
        order_in_program=3,
        exercises=[
            {"exercise_id": str(exercise_mapping["Dumbbell Incline Press"]), "sets": 4, "order_in_session": 1, "notes": "30-45 degree angle"},
            {"exercise_id": str(exercise_mapping["Pull-Ups"]), "sets": 4, "order_in_session": 2, "notes": "Add weight if needed"},
            {"exercise_id": str(exercise_mapping["Dips (Chest Focused)"]), "sets": 3, "order_in_session": 3, "notes": "Lean forward"},
            {"exercise_id": str(exercise_mapping["Dumbbell Row"]), "sets": 3, "order_in_session": 4, "notes": "Each arm"},
            {"exercise_id": str(exercise_mapping["Tricep Pushdown"]), "sets": 3, "order_in_session": 5, "notes": None}
        ],
        total_sets=17
    )
    session.add(ul_upper_b)
    
    # Lower Body B
    ul_lower_b = WorkoutSessionModel(
        id=uuid4(),
        program_id=ul_program.id,
        name="Lower Body B",
        day_number=5,
        order_in_program=4,
        exercises=[
            {"exercise_id": str(exercise_mapping["Leg Press"]), "sets": 4, "order_in_session": 1, "notes": "Full range of motion"},
            {"exercise_id": str(exercise_mapping["Romanian Deadlift"]), "sets": 4, "order_in_session": 2, "notes": None},
            {"exercise_id": str(exercise_mapping["Barbell Back Squat"]), "sets": 3, "order_in_session": 3, "notes": "Lighter weight"},
            {"exercise_id": str(exercise_mapping["Leg Curl"]), "sets": 3, "order_in_session": 4, "notes": None}
        ],
        total_sets=14
    )
    session.add(ul_lower_b)
    
    print(f"✓ Created 'Upper/Lower 4-Day Split' template with 4 sessions")
    
    # ========================================================================
    # TEMPLATE 2: Push/Pull/Legs 6-Day Split
    # ========================================================================
    ppl_program = TrainingProgramModel(
        id=uuid4(),
        name="Push/Pull/Legs 6-Day Split",
        description="High-frequency PPL split for advanced lifters. Train each muscle group twice per week with dedicated push, pull, and leg days.",
        split_type="PUSH_PULL_LEGS",
        structure_type="WEEKLY",
        structure_config={
            "days_per_week": 6,
            "selected_days": ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
        },
        is_template=True,
        created_by_user_id=None,
        organization_id=None,
        duration_weeks=12
    )
    session.add(ppl_program)
    await session.flush()
    
    # Push Day
    ppl_push = WorkoutSessionModel(
        id=uuid4(),
        program_id=ppl_program.id,
        name="Push Day",
        day_number=1,
        order_in_program=1,
        exercises=[
            {"exercise_id": str(exercise_mapping["Barbell Bench Press"]), "sets": 4, "order_in_session": 1, "notes": "Heavy compound"},
            {"exercise_id": str(exercise_mapping["Overhead Press"]), "sets": 4, "order_in_session": 2, "notes": None},
            {"exercise_id": str(exercise_mapping["Dumbbell Incline Press"]), "sets": 3, "order_in_session": 3, "notes": None},
            {"exercise_id": str(exercise_mapping["Dumbbell Lateral Raise"]), "sets": 3, "order_in_session": 4, "notes": None},
            {"exercise_id": str(exercise_mapping["Tricep Pushdown"]), "sets": 3, "order_in_session": 5, "notes": None}
        ],
        total_sets=17
    )
    session.add(ppl_push)
    
    # Pull Day
    ppl_pull = WorkoutSessionModel(
        id=uuid4(),
        program_id=ppl_program.id,
        name="Pull Day",
        day_number=2,
        order_in_program=2,
        exercises=[
            {"exercise_id": str(exercise_mapping["Pull-Ups"]), "sets": 4, "order_in_session": 1, "notes": "Weighted if possible"},
            {"exercise_id": str(exercise_mapping["Barbell Bent-Over Row"]), "sets": 4, "order_in_session": 2, "notes": None},
            {"exercise_id": str(exercise_mapping["Dumbbell Row"]), "sets": 3, "order_in_session": 3, "notes": "Each arm"},
            {"exercise_id": str(exercise_mapping["Face Pulls"]), "sets": 3, "order_in_session": 4, "notes": None},
            {"exercise_id": str(exercise_mapping["Barbell Curl"]), "sets": 3, "order_in_session": 5, "notes": None}
        ],
        total_sets=17
    )
    session.add(ppl_pull)
    
    # Legs Day
    ppl_legs = WorkoutSessionModel(
        id=uuid4(),
        program_id=ppl_program.id,
        name="Legs Day",
        day_number=3,
        order_in_program=3,
        exercises=[
            {"exercise_id": str(exercise_mapping["Barbell Back Squat"]), "sets": 4, "order_in_session": 1, "notes": "Heavy weight"},
            {"exercise_id": str(exercise_mapping["Romanian Deadlift"]), "sets": 4, "order_in_session": 2, "notes": None},
            {"exercise_id": str(exercise_mapping["Leg Press"]), "sets": 3, "order_in_session": 3, "notes": None},
            {"exercise_id": str(exercise_mapping["Leg Curl"]), "sets": 3, "order_in_session": 4, "notes": None},
            {"exercise_id": str(exercise_mapping["Standing Calf Raise"]), "sets": 4, "order_in_session": 5, "notes": None}
        ],
        total_sets=18
    )
    session.add(ppl_legs)
    
    print(f"✓ Created 'Push/Pull/Legs 6-Day Split' template with 3 sessions")
    
    # ========================================================================
    # TEMPLATE 3: Full Body 3-Day Split (Beginner)
    # ========================================================================
    fb_program = TrainingProgramModel(
        id=uuid4(),
        name="Full Body 3-Day Split",
        description="Beginner-friendly full body split. Train all major muscle groups 3x per week for balanced development and frequent practice. Perfect for building strength foundation.",
        split_type="FULL_BODY",
        structure_type="WEEKLY",
        structure_config={
            "days_per_week": 3,
            "selected_days": ["MON", "WED", "FRI"]
        },
        is_template=True,
        created_by_user_id=None,
        organization_id=None,
        duration_weeks=8
    )
    session.add(fb_program)
    await session.flush()
    
    # Full Body Day A
    fb_day_a = WorkoutSessionModel(
        id=uuid4(),
        program_id=fb_program.id,
        name="Full Body Day A",
        day_number=1,
        order_in_program=1,
        exercises=[
            {"exercise_id": str(exercise_mapping["Barbell Back Squat"]), "sets": 3, "order_in_session": 1, "notes": "Focus on form"},
            {"exercise_id": str(exercise_mapping["Barbell Bench Press"]), "sets": 3, "order_in_session": 2, "notes": None},
            {"exercise_id": str(exercise_mapping["Barbell Bent-Over Row"]), "sets": 3, "order_in_session": 3, "notes": None},
            {"exercise_id": str(exercise_mapping["Dumbbell Lateral Raise"]), "sets": 3, "order_in_session": 4, "notes": None},
            {"exercise_id": str(exercise_mapping["Plank"]), "sets": 3, "order_in_session": 5, "notes": "Hold 30-60 seconds"}
        ],
        total_sets=15
    )
    session.add(fb_day_a)
    
    # Full Body Day B
    fb_day_b = WorkoutSessionModel(
        id=uuid4(),
        program_id=fb_program.id,
        name="Full Body Day B",
        day_number=3,
        order_in_program=2,
        exercises=[
            {"exercise_id": str(exercise_mapping["Romanian Deadlift"]), "sets": 3, "order_in_session": 1, "notes": None},
            {"exercise_id": str(exercise_mapping["Overhead Press"]), "sets": 3, "order_in_session": 2, "notes": None},
            {"exercise_id": str(exercise_mapping["Pull-Ups"]), "sets": 3, "order_in_session": 3, "notes": "Use assistance if needed"},
            {"exercise_id": str(exercise_mapping["Barbell Curl"]), "sets": 3, "order_in_session": 4, "notes": None},
            {"exercise_id": str(exercise_mapping["Hanging Leg Raise"]), "sets": 3, "order_in_session": 5, "notes": None}
        ],
        total_sets=15
    )
    session.add(fb_day_b)
    
    # Full Body Day C
    fb_day_c = WorkoutSessionModel(
        id=uuid4(),
        program_id=fb_program.id,
        name="Full Body Day C",
        day_number=5,
        order_in_program=3,
        exercises=[
            {"exercise_id": str(exercise_mapping["Leg Press"]), "sets": 3, "order_in_session": 1, "notes": None},
            {"exercise_id": str(exercise_mapping["Dumbbell Incline Press"]), "sets": 3, "order_in_session": 2, "notes": None},
            {"exercise_id": str(exercise_mapping["Dumbbell Row"]), "sets": 3, "order_in_session": 3, "notes": None},
            {"exercise_id": str(exercise_mapping["Tricep Pushdown"]), "sets": 3, "order_in_session": 4, "notes": None},
            {"exercise_id": str(exercise_mapping["Russian Twist"]), "sets": 3, "order_in_session": 5, "notes": None}
        ],
        total_sets=15
    )
    session.add(fb_day_c)
    
    print(f"✓ Created 'Full Body 3-Day Split' template with 3 sessions")


async def main():
    """Main seed data execution."""
    print("="*70)
    print("HypertroQ Database Seeding")
    print("="*70)
    
    # Get database URL from settings
    database_url = str(settings.DIRECT_URL or settings.DATABASE_URL)
    
    if not database_url:
        print("❌ No database URL found in environment")
        print("   Set DATABASE_URL or DIRECT_URL")
        return
    
    # Create async engine
    engine = create_async_engine(
        database_url,
        echo=False,
        future=True
    )
    
    # Create session factory
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            # Start transaction
            async with session.begin():
                # 1. Create default organization
                org_id = await create_default_organization(session)
                
                # 2. Create admin user
                admin_id = await create_admin_user(session, org_id)
                
                # 3. Seed global exercises
                exercise_mapping = await seed_exercises(session)
                
                # 4. Seed program templates
                await seed_program_templates(session, exercise_mapping)
                
                # Commit transaction
                await session.commit()
        
        print("="*70)
        print("✅ Database seeding complete!")
        print("="*70)
        print("\nSeeded Data Summary:")
        print(f"  • 1 organization (Default Organization)")
        print(f"  • 1 admin user (admin@hypertroq.com)")
        print(f"  • {len(EXERCISES_DATA)} global exercises")
        print(f"  • 3 program templates:")
        print(f"    - Upper/Lower 4-Day Split (4 sessions, 62 total sets)")
        print(f"    - Push/Pull/Legs 6-Day Split (3 sessions, 52 total sets)")
        print(f"    - Full Body 3-Day Split (3 sessions, 45 total sets)")
        print("\n⚠️  Remember to change the admin password in production!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
