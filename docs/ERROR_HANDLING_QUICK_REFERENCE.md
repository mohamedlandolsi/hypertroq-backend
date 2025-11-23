# Error Handling Quick Reference

## Import Statements

```python
# Basic exceptions
from app.core.exceptions import (
    AppException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ValidationException,
    SubscriptionRequiredException,
    RateLimitException,
    ConflictException,
    BadRequestException,
)

# Error codes
from app.core.exceptions import ErrorCode

# Factory functions
from app.core.exceptions import (
    user_not_found,
    invalid_credentials,
    token_expired,
    admin_required,
    pro_tier_required,
    rate_limit_exceeded,
    email_already_registered,
)
```

---

## Common Usage Patterns

### User Not Found
```python
raise user_not_found("550e8400-e29b-41d4-a716-446655440000")
```
**Response**: 404, `USER_NOT_FOUND`

### Invalid Login
```python
raise invalid_credentials()
```
**Response**: 401, `INVALID_CREDENTIALS`

### Token Expired
```python
raise token_expired()
```
**Response**: 401, `TOKEN_EXPIRED`

### Admin Required
```python
raise admin_required()
```
**Response**: 403, `ADMIN_REQUIRED`

### PRO Tier Required
```python
raise pro_tier_required("custom_exercises")
```
**Response**: 402, `PRO_TIER_REQUIRED`

### Rate Limit Exceeded
```python
raise rate_limit_exceeded(
    limit=100,
    window="1 minute",
    retry_after=60
)
```
**Response**: 429, `RATE_LIMIT_EXCEEDED`

### Email Already Registered
```python
raise email_already_registered("user@example.com")
```
**Response**: 409, `EMAIL_ALREADY_REGISTERED`

### Invalid File Type
```python
from app.core.exceptions import invalid_file_type

raise invalid_file_type(["image/jpeg", "image/png"])
```
**Response**: 400, `INVALID_FILE_TYPE`

### File Too Large
```python
from app.core.exceptions import file_too_large

raise file_too_large(5 * 1024 * 1024)  # 5 MB
```
**Response**: 400, `FILE_TOO_LARGE`

---

## Error Response Structure

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found",
    "status_code": 404,
    "timestamp": "2024-01-20T15:30:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "path": "/api/v1/users/123",
    "details": {
      "user_id": "123"
    }
  }
}
```

---

## HTTP Status Codes

| Status | Exception | Use Case |
|--------|-----------|----------|
| 400 | BadRequestException | Invalid operation, file errors |
| 401 | AuthenticationException | Login required, token invalid |
| 402 | SubscriptionRequiredException | PRO features, limits |
| 403 | AuthorizationException | Insufficient permissions |
| 404 | NotFoundException | Resource doesn't exist |
| 409 | ConflictException | Duplicate resource |
| 422 | ValidationException | Invalid input data |
| 429 | RateLimitException | Too many requests |
| 500 | AppException | Internal server error |

---

## Error Codes by Category

### Authentication (401)
- `AUTHENTICATION_REQUIRED`
- `INVALID_CREDENTIALS`
- `TOKEN_EXPIRED`
- `TOKEN_INVALID`
- `EMAIL_NOT_VERIFIED`

### Authorization (403)
- `PERMISSION_DENIED`
- `INSUFFICIENT_PERMISSIONS`
- `ADMIN_REQUIRED`
- `ORGANIZATION_ACCESS_DENIED`

### Not Found (404)
- `RESOURCE_NOT_FOUND`
- `USER_NOT_FOUND`
- `ORGANIZATION_NOT_FOUND`
- `PROGRAM_NOT_FOUND`
- `EXERCISE_NOT_FOUND`

### Validation (422)
- `VALIDATION_ERROR`
- `INVALID_INPUT`
- `MISSING_REQUIRED_FIELD`
- `INVALID_EMAIL`
- `INVALID_PASSWORD`

### Subscription (402)
- `SUBSCRIPTION_REQUIRED`
- `PRO_TIER_REQUIRED`
- `FEATURE_NOT_AVAILABLE`
- `SUBSCRIPTION_EXPIRED`

### Rate Limiting (429)
- `RATE_LIMIT_EXCEEDED`
- `AI_QUERY_LIMIT_EXCEEDED`

### Conflicts (409)
- `RESOURCE_ALREADY_EXISTS`
- `EMAIL_ALREADY_REGISTERED`
- `DUPLICATE_ENTRY`

### Bad Request (400)
- `INVALID_OPERATION`
- `ACCOUNT_DISABLED`
- `INVALID_FILE_TYPE`
- `FILE_TOO_LARGE`

---

## Service Layer Examples

### User Service
```python
class UserService:
    async def get_user(self, user_id: UUID):
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise user_not_found(str(user_id))
        return user
    
    async def create_user(self, email: str):
        existing = await self.repo.get_by_email(email)
        if existing:
            raise email_already_registered(email)
        # Create user...
```

### Organization Service
```python
class OrganizationService:
    async def require_pro(self, org_id: UUID, feature: str):
        org = await self.get_organization(org_id)
        if not org.can_use_feature(feature):
            raise pro_tier_required(feature)
```

### Rate Limiting
```python
async def check_rate_limit(user_id: UUID, limit: int):
    requests = await redis.get(f"rate:{user_id}")
    if requests >= limit:
        raise rate_limit_exceeded(
            limit=limit,
            window="1 hour",
            retry_after=3600
        )
```

---

## Client-Side Handling

### JavaScript
```javascript
try {
  const response = await fetch('/api/v1/users/me');
  const data = await response.json();
  
  if (!response.ok) {
    const { code, message } = data.error;
    
    switch (code) {
      case 'TOKEN_EXPIRED':
        await refreshToken();
        break;
      case 'PRO_TIER_REQUIRED':
        showUpgradeModal();
        break;
      default:
        showError(message);
    }
  }
} catch (err) {
  console.error(err);
}
```

### TypeScript
```typescript
interface ApiError {
  error: {
    code: string;
    message: string;
    status_code: number;
    details?: Record<string, any>;
  };
}

async function apiCall<T>(url: string): Promise<T> {
  const response = await fetch(url);
  
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.error.message);
  }
  
  return response.json();
}
```

---

## Testing

### Unit Test
```python
def test_user_not_found():
    with pytest.raises(NotFoundException) as exc:
        raise user_not_found("123")
    
    assert exc.value.error_code == ErrorCode.USER_NOT_FOUND
    assert exc.value.status_code == 404
```

### Integration Test
```python
def test_get_user_404(client):
    response = client.get("/api/v1/users/123")
    
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "USER_NOT_FOUND"
```

---

## Logging

All errors automatically log:
```python
logger.error(
    "USER_NOT_FOUND: User not found",
    extra={
        "error_code": "USER_NOT_FOUND",
        "status_code": 404,
        "path": "/api/v1/users/123",
        "request_id": "...",
        "client": "192.168.1.1"
    }
)
```

---

## Environment Variables

```bash
# .env
ENVIRONMENT=production  # or "development"
SENTRY_DSN=https://...  # Optional error tracking
```

**Development**: Includes stack traces  
**Production**: Sanitized errors, Sentry integration

---

## Setup in main.py

```python
from app.core.error_handlers import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
```

---

## Cheat Sheet

| Need | Use |
|------|-----|
| User not found | `raise user_not_found(user_id)` |
| Wrong password | `raise invalid_credentials()` |
| Token expired | `raise token_expired()` |
| Need admin | `raise admin_required()` |
| Need PRO | `raise pro_tier_required(feature)` |
| Too many requests | `raise rate_limit_exceeded(limit, window, retry_after)` |
| Email exists | `raise email_already_registered(email)` |
| Invalid file | `raise invalid_file_type(allowed_types)` |
| File too big | `raise file_too_large(max_size)` |
| Generic not found | `raise NotFoundException(message, error_code)` |
| Generic error | `raise AppException(message, error_code, status_code)` |
