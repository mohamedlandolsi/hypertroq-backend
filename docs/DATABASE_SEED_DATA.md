# Database Seed Data Documentation

## Overview
This document describes the seed data populated in the HypertroQ database and how to use the seed script.

## Seed Script Location
```
scripts/seed_data.py
```

## Usage
```bash
# Run from project root
python scripts/seed_data.py
```

## Requirements
- PostgreSQL database running (docker-compose up -d postgres)
- All migrations applied (alembic upgrade head)
- DATABASE_URL or DIRECT_URL environment variable set

## Seeded Data

### 1. Default Organization
- **Name:** Default Organization
- **Subscription Tier:** FREE
- **Subscription Status:** ACTIVE
- **Purpose:** Container for admin user and global data

### 2. Admin User
- **Email:** admin@hypertroq.com
- **Password:** Admin@123 ⚠️ **CHANGE IN PRODUCTION!**
- **Role:** ADMIN
- **Organization:** Default Organization
- **Status:** Active and verified

### 3. Global Exercises (30 Total)

#### Chest (3 exercises)
1. **Barbell Bench Press** - Primary chest builder, compound movement
2. **Dumbbell Incline Press** - Upper chest focus at 30-45 degrees
3. **Dips (Chest Focused)** - Bodyweight chest and tricep builder

#### Back (5 exercises)
4. **Barbell Bent-Over Row** - Back thickness, lat and rhomboid development
5. **Pull-Ups** - Best lat builder, bodyweight
6. **Lat Pulldown** - Pull-up alternative, adjustable resistance
7. **Dumbbell Row** - Unilateral back work, full ROM
8. **Deadlift** - Ultimate full-body compound, posterior chain emphasis

#### Shoulders (3 exercises)
9. **Overhead Press** - Primary shoulder mass builder
10. **Dumbbell Lateral Raise** - Side delt isolation
11. **Face Pulls** - Rear delt and upper back health

#### Arms (4 exercises)
12. **Barbell Curl** - Classic bicep builder
13. **Hammer Curl** - Brachialis and forearm focus
14. **Tricep Pushdown** - Tricep isolation via cable
15. **Close-Grip Bench Press** - Compound tricep movement

#### Legs (7 exercises)
16. **Barbell Back Squat** - King of leg exercises, quad emphasis
17. **Romanian Deadlift** - Best hamstring and glute builder
18. **Leg Press** - Quad-focused machine compound
19. **Bulgarian Split Squat** - Unilateral leg developer
20. **Leg Curl** - Hamstring isolation
21. **Leg Extension** - Quad isolation
22. **Standing Calf Raise** - Primary calf developer

#### Core (4 exercises)
23. **Plank** - Core stability and endurance
24. **Cable Crunch** - Weighted ab flexion
25. **Russian Twist** - Oblique rotational work
26. **Hanging Leg Raise** - Advanced ab exercise

#### Additional Compounds (4 exercises)
27. **Front Squat** - Quad-emphasized squat variation
28. **Chin-Ups** - Supinated pull-up, bicep emphasis
29. **T-Bar Row** - Thick back builder
30. **Hip Thrust** - Best glute isolation exercise

### 4. Program Templates (3 Total)

#### Template 1: Upper/Lower 4-Day Split
- **Split Type:** UPPER_LOWER
- **Structure:** WEEKLY (Mon, Tue, Thu, Fri)
- **Duration:** 8 weeks
- **Sessions:** 4
  - Upper Body A (17 sets) - Bench, Row, OHP, Lateral Raise, Curl
  - Lower Body A (14 sets) - Squat, RDL, Leg Press, Leg Curl
  - Upper Body B (17 sets) - Incline DB, Pull-ups, Dips, DB Row, Pushdown
  - Lower Body B (14 sets) - Leg Press, RDL, Squat (light), Leg Curl
- **Total Volume:** 62 sets/week
- **Target Audience:** Intermediate lifters seeking balanced development

#### Template 2: Push/Pull/Legs 6-Day Split
- **Split Type:** PUSH_PULL_LEGS
- **Structure:** WEEKLY (Mon-Sat)
- **Duration:** 12 weeks
- **Sessions:** 3 (repeated twice weekly)
  - Push Day (17 sets) - Bench, OHP, Incline DB, Lateral Raise, Pushdown
  - Pull Day (17 sets) - Pull-ups, BB Row, DB Row, Face Pulls, Curl
  - Legs Day (18 sets) - Squat, RDL, Leg Press, Leg Curl, Calf Raise
- **Total Volume:** 52 sets/week
- **Target Audience:** Advanced lifters, high-frequency training

#### Template 3: Full Body 3-Day Split
- **Split Type:** FULL_BODY
- **Structure:** WEEKLY (Mon, Wed, Fri)
- **Duration:** 8 weeks
- **Sessions:** 3
  - Full Body A (15 sets) - Squat, Bench, BB Row, Lateral Raise, Plank
  - Full Body B (15 sets) - RDL, OHP, Pull-ups, Curl, Hanging Leg Raise
  - Full Body C (15 sets) - Leg Press, Incline DB, DB Row, Pushdown, Russian Twist
- **Total Volume:** 45 sets/week
- **Target Audience:** Beginners, those returning from break

## Muscle Contribution Mapping

Each exercise includes a `muscle_contributions` JSONB field mapping muscle groups to contribution factors (0.25, 0.5, 0.75, 1.0):

```json
{
  "CHEST": 1.0,
  "FRONT_DELTS": 0.5,
  "TRICEPS": 0.75
}
```

### 18 Muscle Groups
1. CHEST - Pectoralis major/minor
2. LATS - Latissimus dorsi
3. TRAPS_RHOMBOIDS - Upper/mid back
4. FRONT_DELTS - Anterior deltoid
5. SIDE_DELTS - Lateral deltoid
6. REAR_DELTS - Posterior deltoid
7. TRICEPS - Triceps brachii
8. ELBOW_FLEXORS - Biceps + brachialis
9. FOREARMS - Wrist flexors/extensors
10. SPINAL_ERECTORS - Lower back
11. ABS - Rectus abdominis
12. OBLIQUES - External/internal obliques
13. GLUTES - Gluteus maximus/medius
14. QUADS - Quadriceps
15. HAMSTRINGS - Biceps femoris, etc.
16. ADDUCTORS - Inner thigh
17. CALVES - Gastrocnemius/soleus
18. (ADDUCTORS not yet in seed data)

## Equipment Types
- BARBELL - Olympic barbell exercises
- DUMBBELL - Dumbbell exercises
- CABLE - Cable machine exercises
- MACHINE - Plate-loaded or pin-select machines
- BODYWEIGHT - Calisthenics, no equipment

## Script Features

### Idempotency
The script checks for existing data before inserting:
- Won't create duplicate organizations
- Won't create duplicate admin users
- Won't re-seed exercises if 20+ already exist
- Won't create duplicate program templates if 3+ exist

### Transaction Safety
All operations wrapped in a single database transaction - either all succeed or all rollback.

### Error Handling
Comprehensive error messages with stack traces for debugging.

## Testing Seed Data

### Verify Organizations
```sql
SELECT * FROM organizations WHERE name = 'Default Organization';
```

### Verify Admin User
```sql
SELECT id, email, role, is_active, is_verified 
FROM users 
WHERE email = 'admin@hypertroq.com';
```

### Verify Exercises
```sql
SELECT COUNT(*) as total, equipment, COUNT(*) 
FROM exercises 
WHERE is_global = true 
GROUP BY equipment;
```

### Verify Program Templates
```sql
SELECT p.name, p.split_type, COUNT(s.id) as session_count
FROM training_programs p
LEFT JOIN workout_sessions s ON s.program_id = p.id
WHERE p.is_template = true
GROUP BY p.id, p.name, p.split_type;
```

## Re-seeding Strategy

### Fresh Start
```bash
# Drop all data (CAUTION!)
alembic downgrade base
alembic upgrade head
python scripts/seed_data.py
```

### Update Existing
```bash
# Script is idempotent - safe to run multiple times
python scripts/seed_data.py
```

## Production Considerations

1. **Change Admin Password Immediately**
   ```python
   # Via API or direct database update
   UPDATE users 
   SET hashed_password = <new_bcrypt_hash>
   WHERE email = 'admin@hypertroq.com';
   ```

2. **Backup Before Seeding**
   ```bash
   pg_dump -U postgres -d hypertoq > backup_before_seed.sql
   ```

3. **Review Exercise Data**
   - Validate muscle contributions match your domain model
   - Add custom descriptions or images
   - Adjust equipment types if needed

4. **Customize Templates**
   - Modify program templates for your user base
   - Add more templates for niche training styles
   - Adjust set/rep recommendations

## Troubleshooting

### "password cannot be longer than 72 bytes"
This is a bcrypt/Python 3.13 compatibility issue. The script uses a pre-hashed password to avoid this. If you need to change it:
```python
# Generate new hash on Python 3.11 or earlier
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
print(pwd_context.hash("YourNewPassword"))
```

### "Database connection refused"
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Wait for initialization
sleep 5

# Run seed script
python scripts/seed_data.py
```

### "Table does not exist"
```bash
# Apply migrations first
alembic upgrade head

# Then seed
python scripts/seed_data.py
```

## Next Steps

After seeding:
1. ✅ Test admin login via API: POST /api/v1/auth/login
2. ✅ Verify exercises endpoint: GET /api/v1/exercises?is_global=true
3. ✅ Check program templates: GET /api/v1/programs?is_template=true
4. 🔄 Add custom exercises for testing
5. 🔄 Clone templates and create user programs
6. 🔄 Test volume calculation algorithms
