# API Documentation

Complete API reference for HypertroQ Backend.

## Table of Contents

- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Responses](#error-responses)
- [Endpoints](#endpoints)
  - [Authentication & Authorization](#authentication--authorization)
  - [User Management](#user-management)
  - [Exercise Management](#exercise-management)
  - [Program Management](#program-management)
  - [Admin Panel](#admin-panel)
  - [Health & Monitoring](#health--monitoring)

---

## Authentication

HypertroQ uses **JWT (JSON Web Token)** authentication with access and refresh tokens.

### Token Flow

1. **Register** or **Login** to get tokens
2. Include **access token** in `Authorization` header for protected endpoints
3. **Refresh** access token when it expires using refresh token
4. **Logout** to invalidate refresh token

### Authorization Header Format

```http
Authorization: Bearer <access_token>
```

### Token Lifetimes

- **Access Token**: 15 minutes (configurable)
- **Refresh Token**: 7 days (configurable)

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse.

### Default Limits

- **Read operations** (GET): 60 requests/minute
- **Write operations** (POST, PUT, DELETE): 10-20 requests/minute
- **AI operations**: 5-10 requests/minute (tier-dependent)

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640000000
```

### Rate Limit Response (429)

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 30 seconds.",
    "details": {
      "retry_after": 30
    }
  }
}
```

---

## Error Responses

All errors follow a consistent JSON structure.

### Error Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "uuid-here"
  }
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `VALIDATION_ERROR` | Invalid request data |
| 401 | `UNAUTHORIZED` | Missing or invalid token |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Resource already exists |
| 422 | `UNPROCESSABLE_ENTITY` | Semantic validation failed |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |

---

## Endpoints

### Authentication & Authorization

#### 1. Register User

```http
POST /api/v1/auth/register
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "subscription_tier": "free",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

**Errors:**
- `409 CONFLICT` - Email already registered

---

#### 2. Login

```http
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):** Same as register

**Errors:**
- `401 UNAUTHORIZED` - Invalid credentials
- `403 FORBIDDEN` - Account deactivated

---

#### 3. Refresh Token

```http
POST /api/v1/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**
- `401 UNAUTHORIZED` - Invalid or expired refresh token

---

#### 4. Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

---

#### 5. Request Password Reset

```http
POST /api/v1/auth/forgot-password
```

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Response (200):**
```json
{
  "message": "Password reset email sent if account exists"
}
```

*(Always returns 200 to prevent email enumeration)*

---

#### 6. Reset Password

```http
POST /api/v1/auth/reset-password
```

**Request Body:**
```json
{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePass123!"
}
```

**Response (200):**
```json
{
  "message": "Password successfully reset"
}
```

**Errors:**
- `400 BAD_REQUEST` - Invalid or expired token

---

#### 7. Verify Email

```http
POST /api/v1/auth/verify-email
```

**Request Body:**
```json
{
  "token": "verification-token-from-email"
}
```

**Response (200):**
```json
{
  "message": "Email successfully verified"
}
```

---

### User Management

#### 1. Get Current User

```http
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": "uuid",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "subscription_tier": "pro",
  "subscription_status": "active",
  "ai_queries_used": 45,
  "ai_queries_limit": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

---

#### 2. Update User Profile

```http
PUT /api/v1/users/me
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "full_name": "John Smith",
  "email": "john.smith@example.com"
}
```

**Response (200):** Returns updated user object

**Errors:**
- `409 CONFLICT` - Email already in use

---

#### 3. Change Password

```http
POST /api/v1/users/me/change-password
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass123!"
}
```

**Response (200):**
```json
{
  "message": "Password successfully changed"
}
```

**Errors:**
- `401 UNAUTHORIZED` - Current password incorrect

---

#### 4. Delete Account

```http
DELETE /api/v1/users/me
Authorization: Bearer <access_token>
```

**Response (204):** No content

---

### Exercise Management

#### 1. List Global Exercises

```http
GET /api/v1/exercises?page=1&limit=20&search=bench&equipment=BARBELL&muscle_group=CHEST
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Results per page (default: 20, max: 100)
- `search` (string): Search by name
- `equipment` (enum): Filter by equipment type
- `muscle_group` (enum): Filter by primary muscle
- `difficulty` (enum): BEGINNER, INTERMEDIATE, ADVANCED

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Barbell Bench Press",
      "description": "Classic compound chest exercise",
      "equipment": "BARBELL",
      "muscle_contributions": {
        "CHEST": 1.0,
        "FRONT_DELTS": 0.5,
        "TRICEPS": 0.5
      },
      "difficulty": "INTERMEDIATE",
      "is_global": true,
      "created_by_user_id": null,
      "image_url": "https://storage.googleapis.com/...",
      "video_url": "https://storage.googleapis.com/..."
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "has_more": true
  }
}
```

---

#### 2. Get Exercise by ID

```http
GET /api/v1/exercises/{exercise_id}
```

**Response (200):** Single exercise object

**Errors:**
- `404 NOT_FOUND` - Exercise not found

---

#### 3. Create Custom Exercise (Pro Only)

```http
POST /api/v1/exercises
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "Cable Fly Variation",
  "description": "Modified cable fly for upper chest",
  "equipment": "CABLE",
  "muscle_contributions": {
    "CHEST": 1.0,
    "FRONT_DELTS": 0.25
  },
  "difficulty": "INTERMEDIATE"
}
```

**Response (201):** Created exercise object

**Errors:**
- `403 FORBIDDEN` - Pro subscription required
- `409 CONFLICT` - Exercise name already exists for user

---

#### 4. Update Custom Exercise

```http
PUT /api/v1/exercises/{exercise_id}
Authorization: Bearer <access_token>
```

**Request Body:** Partial exercise update

**Response (200):** Updated exercise object

**Errors:**
- `403 FORBIDDEN` - Not exercise owner or not a custom exercise
- `404 NOT_FOUND` - Exercise not found

---

#### 5. Delete Custom Exercise

```http
DELETE /api/v1/exercises/{exercise_id}
Authorization: Bearer <access_token>
```

**Response (204):** No content

**Errors:**
- `403 FORBIDDEN` - Not exercise owner or not a custom exercise
- `409 CONFLICT` - Exercise in use by programs

---

#### 6. List User's Custom Exercises

```http
GET /api/v1/exercises/me?page=1&limit=20
Authorization: Bearer <access_token>
```

**Response (200):** List of user's custom exercises

---

#### 7. Get Exercise Analytics

```http
GET /api/v1/exercises/{exercise_id}/analytics
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "usage_count": 45,
  "programs_using": 12,
  "total_volume_performed": 12500,
  "average_sets_per_session": 3.5
}
```

---

#### 8. Search Exercises (Semantic)

```http
POST /api/v1/exercises/search
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "query": "exercises for building bigger arms",
  "limit": 10
}
```

**Response (200):** Semantically similar exercises

---

#### 9. Get Equipment Types

```http
GET /api/v1/exercises/equipment-types
```

**Response (200):**
```json
{
  "equipment_types": [
    "BARBELL",
    "DUMBBELL",
    "CABLE",
    "MACHINE",
    "BODYWEIGHT",
    "RESISTANCE_BAND",
    "KETTLEBELL",
    "OTHER"
  ]
}
```

---

#### 10. Get Muscle Groups

```http
GET /api/v1/exercises/muscle-groups
```

**Response (200):**
```json
{
  "muscle_groups": [
    "CHEST", "LATS", "TRAPS", "FRONT_DELTS", "SIDE_DELTS",
    "REAR_DELTS", "TRICEPS", "ELBOW_FLEXORS", "FOREARMS",
    "SPINAL_ERECTORS", "ABS", "OBLIQUES", "GLUTES",
    "QUADS", "HAMSTRINGS", "ADDUCTORS", "CALVES"
  ]
}
```

---

### Program Management

#### 1. List Programs

```http
GET /api/v1/programs?page=1&limit=20&structure_type=WEEKLY&frequency=3
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page`, `limit`: Pagination
- `structure_type`: WEEKLY, CYCLIC
- `frequency`: Number of training days per week
- `is_template`: Filter templates (admin-created)

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Upper/Lower 4-Day Split",
      "description": "Classic upper/lower split for intermediate lifters",
      "structure_type": "WEEKLY",
      "frequency": 4,
      "is_template": false,
      "created_by": "uuid",
      "sessions_count": 4,
      "total_exercises": 24,
      "estimated_duration_minutes": 60,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "meta": { "page": 1, "limit": 20, "total": 10, "has_more": false }
}
```

---

#### 2. Get Program by ID

```http
GET /api/v1/programs/{program_id}
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": "uuid",
  "name": "Upper/Lower 4-Day Split",
  "description": "...",
  "structure_type": "WEEKLY",
  "frequency": 4,
  "sessions": [
    {
      "id": "uuid",
      "name": "Upper A",
      "day_of_week": 0,
      "order_index": 0,
      "exercises": [
        {
          "id": "uuid",
          "exercise_id": "uuid",
          "exercise_name": "Barbell Bench Press",
          "sets": 4,
          "reps": "8-12",
          "order_index": 0
        }
      ]
    }
  ],
  "volume_per_muscle": {
    "CHEST": 12.5,
    "LATS": 14.0,
    "QUADS": 16.0
  }
}
```

---

#### 3. Create Program

```http
POST /api/v1/programs
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "My Custom Program",
  "description": "Tailored program for my goals",
  "structure_type": "WEEKLY",
  "frequency": 3,
  "sessions": [
    {
      "name": "Push Day",
      "day_of_week": 0,
      "exercises": [
        {
          "exercise_id": "uuid",
          "sets": 4,
          "reps": "8-12"
        }
      ]
    }
  ]
}
```

**Response (201):** Created program object

**Errors:**
- `403 FORBIDDEN` - Pro subscription required for custom programs

---

#### 4. Update Program

```http
PUT /api/v1/programs/{program_id}
Authorization: Bearer <access_token>
```

**Request Body:** Partial program update

**Response (200):** Updated program object

**Errors:**
- `403 FORBIDDEN` - Not program owner

---

#### 5. Delete Program

```http
DELETE /api/v1/programs/{program_id}
Authorization: Bearer <access_token>
```

**Response (204):** No content

**Errors:**
- `403 FORBIDDEN` - Not program owner or is template

---

#### 6. Clone Program

```http
POST /api/v1/programs/{program_id}/clone
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "new_name": "My Modified Upper/Lower"
}
```

**Response (201):** Cloned program object

---

#### 7. Calculate Program Volume

```http
GET /api/v1/programs/{program_id}/volume
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "volume_per_muscle": {
    "CHEST": 12.5,
    "LATS": 14.0,
    "FRONT_DELTS": 6.5,
    "TRICEPS": 11.0,
    "QUADS": 16.0,
    "HAMSTRINGS": 10.0
  },
  "warnings": [
    {
      "muscle": "REAR_DELTS",
      "current_volume": 4.0,
      "status": "LOW",
      "recommendation": "Add 6-10 more sets for optimal hypertrophy"
    }
  ]
}
```

---

#### 8. Generate Program Schedule (AI)

```http
POST /api/v1/programs/{program_id}/generate-schedule
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "start_date": "2024-01-15",
  "duration_weeks": 8,
  "preferences": {
    "focus_muscles": ["CHEST", "LATS"],
    "available_equipment": ["BARBELL", "DUMBBELL"]
  }
}
```

**Response (200):**
```json
{
  "schedule": [
    {
      "week": 1,
      "sessions": [
        {
          "date": "2024-01-15",
          "session_name": "Push Day",
          "exercises": [...]
        }
      ]
    }
  ],
  "ai_notes": "Progressive overload applied weeks 1-4, deload week 5"
}
```

**Errors:**
- `403 FORBIDDEN` - AI query limit exceeded (free tier)
- `429 RATE_LIMIT_EXCEEDED` - Too many AI requests

---

#### 9. Get Program Templates

```http
GET /api/v1/programs/templates?page=1&limit=20
```

**Response (200):** List of admin-created program templates

---

#### 10. Get Program Analytics

```http
GET /api/v1/programs/{program_id}/analytics
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "completions": 5,
  "average_adherence": 0.85,
  "total_volume_performed": 25000,
  "favorite_sessions": ["Push Day", "Leg Day"]
}
```

---

### Admin Panel

*(All admin endpoints require `is_superuser=true`)*

#### 1. List All Users

```http
GET /api/v1/admin/users?page=1&limit=20&tier=pro&is_active=true
Authorization: Bearer <admin_access_token>
```

**Response (200):** Paginated list of all users

---

#### 2. Get User by ID

```http
GET /api/v1/admin/users/{user_id}
Authorization: Bearer <admin_access_token>
```

**Response (200):** Full user details including audit logs

---

#### 3. Update User

```http
PUT /api/v1/admin/users/{user_id}
Authorization: Bearer <admin_access_token>
```

**Request Body:**
```json
{
  "subscription_tier": "pro",
  "subscription_status": "active",
  "is_active": true
}
```

**Response (200):** Updated user object

---

#### 4. Delete User

```http
DELETE /api/v1/admin/users/{user_id}
Authorization: Bearer <admin_access_token>
```

**Response (204):** No content (soft delete)

---

#### 5. Reset User Password

```http
POST /api/v1/admin/users/{user_id}/reset-password
Authorization: Bearer <admin_access_token>
```

**Response (200):**
```json
{
  "temporary_password": "TempPass123!"
}
```

---

#### 6. Grant/Revoke Admin

```http
POST /api/v1/admin/users/{user_id}/grant-admin
DELETE /api/v1/admin/users/{user_id}/revoke-admin
Authorization: Bearer <admin_access_token>
```

**Response (200):** Updated user object

---

#### 7. List All Organizations

```http
GET /api/v1/admin/organizations?page=1&limit=20
Authorization: Bearer <admin_access_token>
```

**Response (200):** Paginated organizations list

---

#### 8. Create Global Exercise

```http
POST /api/v1/admin/exercises
Authorization: Bearer <admin_access_token>
```

**Request Body:** Same as user exercise creation

**Response (201):** Global exercise (is_global=true)

---

#### 9. Update Global Exercise

```http
PUT /api/v1/admin/exercises/{exercise_id}
Authorization: Bearer <admin_access_token>
```

**Response (200):** Updated global exercise

---

#### 10. Delete Global Exercise

```http
DELETE /api/v1/admin/exercises/{exercise_id}
Authorization: Bearer <admin_access_token>
```

**Response (204):** No content

---

#### 11. Create Program Template

```http
POST /api/v1/admin/programs/templates
Authorization: Bearer <admin_access_token>
```

**Request Body:** Same as program creation

**Response (201):** Program template (is_template=true)

---

#### 12. Get System Stats

```http
GET /api/v1/admin/stats
Authorization: Bearer <admin_access_token>
```

**Response (200):**
```json
{
  "total_users": 1250,
  "active_users_30d": 850,
  "total_programs": 3200,
  "total_exercises": 450,
  "ai_queries_30d": 12500,
  "revenue_30d": 4500.00,
  "subscriptions": {
    "free": 800,
    "pro": 450
  }
}
```

---

#### 13. View Audit Logs

```http
GET /api/v1/admin/audit-logs?user_id=uuid&action=LOGIN&from=2024-01-01&to=2024-01-31
Authorization: Bearer <admin_access_token>
```

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "action": "LOGIN",
      "resource_type": "user",
      "resource_id": "uuid",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "meta": { "page": 1, "limit": 20, "total": 500 }
}
```

---

#### 14. Export Data (CSV/JSON)

```http
POST /api/v1/admin/export
Authorization: Bearer <admin_access_token>
```

**Request Body:**
```json
{
  "resource": "users",
  "format": "csv",
  "filters": {
    "tier": "pro",
    "created_after": "2024-01-01"
  }
}
```

**Response (200):**
```json
{
  "download_url": "https://storage.googleapis.com/exports/users_2024-01-15.csv",
  "expires_at": "2024-01-16T10:30:00Z"
}
```

---

#### 15. Bulk User Operations

```http
POST /api/v1/admin/users/bulk
Authorization: Bearer <admin_access_token>
```

**Request Body:**
```json
{
  "action": "UPDATE_TIER",
  "user_ids": ["uuid1", "uuid2", "uuid3"],
  "data": {
    "subscription_tier": "pro"
  }
}
```

**Response (200):**
```json
{
  "updated": 3,
  "failed": 0,
  "errors": []
}
```

---

### Health & Monitoring

#### 1. Health Check

```http
GET /api/v1/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "0.1.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

#### 2. Readiness Check

```http
GET /api/v1/health/ready
```

**Response (200):** Same as health check

**Response (503):** Service unavailable if dependencies down

---

#### 3. Liveness Check

```http
GET /api/v1/health/live
```

**Response (200):**
```json
{
  "status": "alive"
}
```

---

## Advanced Features

### Pagination

All list endpoints support pagination:

```http
GET /api/v1/exercises?page=2&limit=50
```

**Response includes meta:**
```json
{
  "data": [...],
  "meta": {
    "page": 2,
    "limit": 50,
    "total": 150,
    "has_more": true
  }
}
```

### Filtering

Many endpoints support query filters:

```http
GET /api/v1/exercises?equipment=BARBELL&difficulty=INTERMEDIATE&muscle_group=CHEST
```

### Sorting

Use `sort` and `order` parameters:

```http
GET /api/v1/programs?sort=created_at&order=desc
```

### Search

Full-text search available:

```http
GET /api/v1/exercises?search=bench+press
```

Semantic search for AI-powered results:

```http
POST /api/v1/exercises/search
{
  "query": "exercises for building bigger arms",
  "limit": 10
}
```

---

## Webhooks

### LemonSqueezy Payment Webhooks

```http
POST /api/v1/webhooks/lemonsqueezy
X-Signature: <webhook-signature>
```

**Events:**
- `subscription.created` - New subscription
- `subscription.updated` - Subscription modified
- `subscription.cancelled` - Subscription cancelled
- `payment.succeeded` - Payment processed
- `payment.failed` - Payment failed

**Webhook verification:**
- Signature validated using `LEMONSQUEEZY_WEBHOOK_SECRET`
- Idempotency key prevents duplicate processing

---

## Best Practices

### 1. Always Use HTTPS in Production
```http
https://api.hypertroq.com/api/v1/*
```

### 2. Store Tokens Securely
- Use secure HTTP-only cookies
- Or encrypted localStorage/sessionStorage
- Never expose tokens in URLs

### 3. Handle Token Expiration
```javascript
// Pseudocode
if (response.status === 401) {
  const newToken = await refreshAccessToken();
  return retryRequest(newToken);
}
```

### 4. Implement Retry Logic
```javascript
// Exponential backoff for 429 and 5xx errors
async function retryRequest(url, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    const response = await fetch(url);
    if (response.ok) return response;
    if (response.status === 429) {
      await sleep(2 ** i * 1000); // 1s, 2s, 4s
    }
  }
}
```

### 5. Validate Input Client-Side
- Validate before sending requests
- Reduces unnecessary API calls
- Improves UX with immediate feedback

---

## Code Examples

### Python Client

See `examples/python_client.py` for complete implementation.

```python
import requests

class HypertroQClient:
    def __init__(self, base_url, access_token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def get_exercises(self, page=1, limit=20):
        response = requests.get(
            f"{self.base_url}/api/v1/exercises",
            params={"page": page, "limit": limit},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
```

### JavaScript/TypeScript Client

```typescript
class HypertroQClient {
  constructor(
    private baseURL: string,
    private accessToken: string
  ) {}

  async getExercises(page = 1, limit = 20) {
    const response = await fetch(
      `${this.baseURL}/api/v1/exercises?page=${page}&limit=${limit}`,
      {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return response.json();
  }
}
```

---

## Changelog

### v0.1.0 (Current)
- Initial API release
- Authentication & authorization
- Exercise management (CRUD)
- Program management (CRUD)
- Admin panel
- Health checks

### Upcoming Features
- Workout logging and tracking
- Progress photos and measurements
- Social features (sharing programs)
- AI coaching recommendations
- Mobile app push notifications

---

## Support

For API issues or questions:
- 📧 Email: api-support@hypertroq.com
- 🐛 GitHub Issues: https://github.com/yourusername/hypertroq-backend/issues
- 📖 Interactive Docs: http://localhost:8000/docs

---

**Last Updated**: January 2024
