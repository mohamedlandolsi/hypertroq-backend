# Training Program API Reference

Complete reference for training program management endpoints.

## Base URL

```
/api/v1/programs
```

## Authentication

All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

## Endpoints Overview

| Method | Endpoint | Description | Auth Required | Rate Limit |
|--------|----------|-------------|---------------|------------|
| GET | `/programs` | List programs with filtering | Yes | None |
| GET | `/programs/{id}` | Get program details | Yes | None |
| POST | `/programs` | Create custom program | Pro/Admin | 10/min |
| POST | `/programs/{template_id}/clone` | Clone template | Pro/Admin | 20/hour |
| PUT | `/programs/{id}` | Update program | Owner | 30/min |
| DELETE | `/programs/{id}` | Delete program | Owner | 10/hour |
| GET | `/programs/{id}/stats` | Get volume statistics | Yes | None |
| POST | `/programs/{id}/sessions` | Add session | Owner | 20/min |
| PUT | `/programs/{id}/sessions/{session_id}` | Update session | Owner | 30/min |
| DELETE | `/programs/{id}/sessions/{session_id}` | Delete session | Owner | 10/hour |

---

## Program Endpoints

### 1. List Programs

```http
GET /api/v1/programs
```

**Query Parameters:**
- `search` (optional): Search term for name/description
- `split_type` (optional): Filter by split type (UPPER_LOWER, PUSH_PULL_LEGS, etc.)
- `structure_type` (optional): Filter by structure (WEEKLY, CYCLIC)
- `is_template` (optional): Filter templates (true) vs user programs (false)
- `skip` (optional, default: 0): Pagination offset
- `limit` (optional, default: 20, max: 100): Items per page

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Upper/Lower 4-Day Split",
      "description": "Classic upper/lower split",
      "split_type": "UPPER_LOWER",
      "structure_type": "WEEKLY",
      "is_template": true,
      "duration_weeks": 8,
      "session_count": 4,
      "created_at": "2025-11-23T10:00:00Z",
      "updated_at": "2025-11-23T10:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

**Access:**
- Returns admin templates (visible to all)
- Returns user's organization programs

---

### 2. Get Program Details

```http
GET /api/v1/programs/{program_id}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Upper/Lower 4-Day Split",
  "description": "Classic upper/lower split",
  "split_type": "UPPER_LOWER",
  "structure_type": "WEEKLY",
  "structure_config": {
    "days_per_week": 4,
    "selected_days": ["MON", "TUE", "THU", "FRI"]
  },
  "is_template": true,
  "duration_weeks": 8,
  "sessions": [
    {
      "id": "uuid",
      "program_id": "uuid",
      "name": "Upper Body A",
      "day_number": 1,
      "order_in_program": 1,
      "exercises": [
        {
          "exercise_id": "uuid",
          "sets": 3,
          "order_in_session": 1,
          "notes": "Focus on form"
        }
      ],
      "total_sets": 15,
      "exercise_count": 5
    }
  ],
  "stats": {
    "total_sessions": 4,
    "total_sets": 60,
    "avg_sets_per_session": 15.0,
    "weekly_volume": [
      {
        "muscle": "CHEST",
        "muscle_name": "Chest",
        "sets_per_week": 16.0,
        "status": "optimal"
      }
    ],
    "training_frequency": 4.0
  },
  "created_at": "2025-11-23T10:00:00Z",
  "updated_at": "2025-11-23T10:00:00Z"
}
```

**Errors:**
- `404`: Program not found or not accessible

---

### 3. Create Custom Program

```http
POST /api/v1/programs
```

**Requirements:**
- Pro subscription or admin role
- Verified email
- Rate limit: 10 requests/minute

**Request Body:**
```json
{
  "name": "My Custom Program",
  "description": "Customized for my goals",
  "split_type": "UPPER_LOWER",
  "structure_type": "WEEKLY",
  "structure_config": {
    "days_per_week": 4,
    "selected_days": ["MON", "TUE", "THU", "FRI"]
  },
  "duration_weeks": 8,
  "sessions": [
    {
      "name": "Upper Body A",
      "day_number": 1,
      "order_in_program": 1,
      "exercises": [
        {
          "exercise_id": "uuid",
          "sets": 3,
          "order_in_session": 1,
          "notes": "Focus on form"
        }
      ]
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "name": "My Custom Program",
  "is_template": false,
  "organization_id": "uuid",
  "sessions": [...],
  "stats": {...}
}
```

**Errors:**
- `400`: Invalid program data
- `403`: Pro subscription required or email not verified
- `429`: Rate limit exceeded

---

### 4. Clone Template Program

```http
POST /api/v1/programs/{template_id}/clone
```

**Requirements:**
- Pro subscription or admin role
- Verified email
- Rate limit: 20 clones/hour

**Request Body:**
```json
{
  "new_name": "My Upper/Lower Split"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "name": "My Upper/Lower Split",
  "is_template": false,
  "organization_id": "uuid",
  "sessions": [...],
  "stats": {...}
}
```

**What gets cloned:**
- Program structure (split, schedule)
- All sessions with exercises
- Exercise sets and ordering
- Exercise notes

**What's customized:**
- New UUID
- Custom name (or default "My {template_name}")
- Organization ownership
- Template flag set to false

**Errors:**
- `403`: Pro subscription required
- `404`: Template not found
- `429`: Rate limit exceeded

---

### 5. Update Program

```http
PUT /api/v1/programs/{program_id}
```

**Requirements:**
- Program ownership
- Verified email
- Rate limit: 30 updates/minute

**Request Body:**
```json
{
  "name": "Updated Program Name",
  "description": "Updated description",
  "duration_weeks": 12
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Updated Program Name",
  "description": "Updated description",
  "duration_weeks": 12,
  ...
}
```

**What you can update:**
- Name
- Description
- Duration (weeks)

**What you cannot update:**
- Split type (create new program)
- Structure type/config (create new program)
- Template programs (read-only)

**Errors:**
- `403`: Not authorized (not owner or template)
- `404`: Program not found
- `429`: Rate limit exceeded

---

### 6. Delete Program

```http
DELETE /api/v1/programs/{program_id}
```

**Requirements:**
- Program ownership
- Verified email
- Rate limit: 10 deletions/hour

**Response:** `204 No Content`

**Cascade behavior:**
- Deletes all sessions
- Deletes all exercise configurations
- Cannot be undone

**Errors:**
- `403`: Not authorized or template
- `404`: Program not found
- `429`: Rate limit exceeded

---

### 7. Get Program Statistics

```http
GET /api/v1/programs/{program_id}/stats
```

**Response:** `200 OK`
```json
{
  "total_sessions": 4,
  "total_sets": 60,
  "avg_sets_per_session": 15.0,
  "weekly_volume": [
    {
      "muscle": "CHEST",
      "muscle_name": "Chest",
      "sets_per_week": 16.0,
      "status": "optimal"
    },
    {
      "muscle": "QUADS",
      "muscle_name": "Quadriceps",
      "sets_per_week": 8.0,
      "status": "low"
    }
  ],
  "training_frequency": 4.0
}
```

**Volume Status:**
- `low` (< 10 sets/week): May be insufficient
- `optimal` (10-20 sets/week): Ideal for hypertrophy
- `high` (20-25 sets/week): Advanced, near recovery limit
- `excessive` (> 25 sets/week): May exceed recovery

**Errors:**
- `404`: Program not found

---

## Session Endpoints

### 8. Add Session to Program

```http
POST /api/v1/programs/{program_id}/sessions
```

**Requirements:**
- Program ownership
- Verified email
- Rate limit: 20 sessions/minute

**Request Body:**
```json
{
  "name": "Upper Body A",
  "day_number": 1,
  "order_in_program": 1,
  "exercises": [
    {
      "exercise_id": "uuid",
      "sets": 3,
      "order_in_session": 1,
      "notes": "Focus on controlled negatives"
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "program_id": "uuid",
  "name": "Upper Body A",
  "day_number": 1,
  "order_in_program": 1,
  "exercises": [...],
  "total_sets": 15,
  "exercise_count": 5
}
```

**Validation:**
- At least 1 exercise required
- Exercise IDs must exist and be accessible
- Day number must be unique within program
- Sets: 1-10 per exercise

**Errors:**
- `400`: Invalid session data
- `403`: Not authorized
- `404`: Program or exercise not found
- `429`: Rate limit exceeded

---

### 9. Update Session

```http
PUT /api/v1/programs/{program_id}/sessions/{session_id}
```

**Requirements:**
- Program ownership (via session)
- Verified email
- Rate limit: 30 updates/minute

**Request Body:**
```json
{
  "name": "Updated Session Name",
  "day_number": 2,
  "order_in_program": 2,
  "exercises": [...]
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Updated Session Name",
  "day_number": 2,
  "exercises": [...],
  "total_sets": 18
}
```

**What you can update:**
- Session name
- Day number (must be unique)
- Order in program
- Exercise list (add/remove/reorder)

**Effects:**
- Total sets recalculated
- Program volume statistics updated

**Errors:**
- `400`: Invalid update data
- `403`: Not authorized
- `404`: Session not found
- `429`: Rate limit exceeded

---

### 10. Delete Session

```http
DELETE /api/v1/programs/{program_id}/sessions/{session_id}
```

**Requirements:**
- Program ownership (via session)
- Verified email
- Program must have at least 2 sessions
- Rate limit: 10 deletions/hour

**Response:** `204 No Content`

**Effects:**
- Session permanently deleted
- Exercise configurations removed
- Program stats updated

**Validation:**
- Cannot delete last session (program must have ≥1 session)

**Errors:**
- `400`: Cannot delete last session
- `403`: Not authorized
- `404`: Session not found
- `429`: Rate limit exceeded

---

## Split Types

Available split types:
- `UPPER_LOWER`: Upper/Lower body split
- `PUSH_PULL_LEGS`: Push/Pull/Legs split
- `FULL_BODY`: Full body workouts
- `BRO_SPLIT`: Body part per day (Bro Split)
- `ARNOLD_SPLIT`: Push/Pull/Legs Arnold split
- `CUSTOM`: User-defined split

## Structure Types

### Weekly Structure
Fixed days per week (Mon, Wed, Fri)

**Config:**
```json
{
  "days_per_week": 3,
  "selected_days": ["MON", "WED", "FRI"]
}
```

### Cyclic Structure
Repeating on/off pattern (3 on, 1 off)

**Config:**
```json
{
  "days_on": 3,
  "days_off": 1
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid data or validation failed |
| 401 | Unauthorized - Not authenticated |
| 403 | Forbidden - Not authorized or Pro required |
| 404 | Not Found - Resource doesn't exist or not accessible |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Rate Limits

| Endpoint Type | Limit | Window |
|--------------|-------|--------|
| List/Get | None | - |
| Create Program | 10 | 1 minute |
| Clone Template | 20 | 1 hour |
| Update Program | 30 | 1 minute |
| Delete Program | 10 | 1 hour |
| Add Session | 20 | 1 minute |
| Update Session | 30 | 1 minute |
| Delete Session | 10 | 1 hour |

## Volume Recommendations

| Status | Sets/Week | Description |
|--------|-----------|-------------|
| Low | < 10 | May be insufficient for hypertrophy |
| Optimal | 10-20 | Ideal range for muscle growth |
| High | 20-25 | Advanced volume, near recovery limit |
| Excessive | > 25 | May exceed recovery capacity |

## Examples

### Create a 4-Day Upper/Lower Program

```bash
curl -X POST https://api.hypertroq.com/api/v1/programs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Upper/Lower Split",
    "description": "4-day upper/lower for intermediate",
    "split_type": "UPPER_LOWER",
    "structure_type": "WEEKLY",
    "structure_config": {
      "days_per_week": 4,
      "selected_days": ["MON", "TUE", "THU", "FRI"]
    },
    "duration_weeks": 8,
    "sessions": [
      {
        "name": "Upper Body A",
        "day_number": 1,
        "order_in_program": 1,
        "exercises": [
          {
            "exercise_id": "bench-press-uuid",
            "sets": 3,
            "order_in_session": 1
          }
        ]
      }
    ]
  }'
```

### Clone a Template

```bash
curl -X POST https://api.hypertroq.com/api/v1/programs/{template_id}/clone \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_name": "My PPL Program"
  }'
```

### Get Program Volume Statistics

```bash
curl -X GET https://api.hypertroq.com/api/v1/programs/{program_id}/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Testing

Swagger documentation available at: `http://localhost:8000/docs`

Interactive API testing and examples available in the Swagger UI.
