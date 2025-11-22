# Authentication API Testing Guide

## Overview
This guide provides examples for testing all authentication endpoints using curl and explains expected responses.

## Prerequisites
- Backend server running on `http://localhost:8000`
- Redis running (optional - falls back to in-memory)

---

## 1. User Registration

**Endpoint:** `POST /api/v1/auth/register`  
**Rate Limit:** 3 requests per 5 minutes per IP

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecureP@ssw0rd123",
    "full_name": "John Doe",
    "organization_name": "Acme Fitness"
  }'
```

**Success Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Response (400) - Email exists:**
```json
{
  "detail": "An account with this email already exists"
}
```

**Error Response (422) - Weak password:**
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Password must contain at least one uppercase letter",
      "type": "value_error"
    }
  ]
}
```

---

## 2. User Login

**Endpoint:** `POST /api/v1/auth/login`  
**Rate Limit:** 10 requests per minute per IP

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecureP@ssw0rd123"
  }'
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Response (401) - Invalid credentials:**
```json
{
  "detail": "Invalid email or password"
}
```

**Error Response (403) - Inactive account:**
```json
{
  "detail": "Your account has been deactivated. Please contact support."
}
```

---

## 3. Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh`  
**Rate Limit:** 10 requests per minute per IP

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Response (401) - Invalid token:**
```json
{
  "detail": "Invalid or expired token"
}
```

---

## 4. Get Current User

**Endpoint:** `GET /api/v1/auth/me`  
**Authentication:** Required

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Success Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "role": "ADMIN",
  "organization_id": "660e8400-e29b-41d4-a716-446655440000",
  "is_verified": false
}
```

**Error Response (401) - Missing or invalid token:**
```json
{
  "detail": "Could not validate credentials"
}
```

---

## 5. Verify Email

**Endpoint:** `POST /api/v1/auth/verify-email/{token}`  
**Note:** Token is sent to user's email after registration

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-email/abc123def456... \
  -H "Content-Type: application/json"
```

**Success Response (200):**
```json
{
  "message": "Email verified successfully"
}
```

**Error Response (401) - Invalid token:**
```json
{
  "detail": "Invalid or expired verification token"
}
```

---

## 6. Request Password Reset

**Endpoint:** `POST /api/v1/auth/password-reset/request`  
**Rate Limit:** 5 requests per minute per IP

```bash
curl -X POST http://localhost:8000/api/v1/auth/password-reset/request \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com"
  }'
```

**Success Response (200) - Always returns this for security:**
```json
{
  "message": "If an account exists with this email, a password reset link has been sent."
}
```

---

## 7. Confirm Password Reset

**Endpoint:** `POST /api/v1/auth/password-reset/confirm`  
**Rate Limit:** 10 requests per minute per IP

```bash
curl -X POST http://localhost:8000/api/v1/auth/password-reset/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "token": "xyz789abc123...",
    "new_password": "NewSecureP@ssw0rd456"
  }'
```

**Success Response (200):**
```json
{
  "message": "Password reset successfully"
}
```

**Error Response (401) - Invalid token:**
```json
{
  "detail": "Invalid or expired reset token"
}
```

---

## Rate Limiting

All endpoints include rate limiting headers in responses:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1700000000
```

**Rate Limit Exceeded Response (429):**
```json
{
  "detail": "Rate limit exceeded. Maximum 10 requests per 60 seconds."
}
```

Headers when rate limited:
```
Retry-After: 45
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1700000045
```

---

## Complete Workflow Example

### 1. Register a new user
```bash
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#",
    "full_name": "Test User",
    "organization_name": "Test Org"
  }')

# Extract access token
ACCESS_TOKEN=$(echo $RESPONSE | jq -r '.access_token')
REFRESH_TOKEN=$(echo $RESPONSE | jq -r '.refresh_token')
```

### 2. Get current user info
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 3. Refresh the access token
```bash
NEW_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")

NEW_ACCESS_TOKEN=$(echo $NEW_RESPONSE | jq -r '.access_token')
```

### 4. Use new access token
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $NEW_ACCESS_TOKEN"
```

---

## Testing Rate Limiting

### Test login rate limit (10 requests per minute)
```bash
for i in {1..15}; do
  echo "Request $i:"
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "wrong"
    }' \
    -w "\nStatus: %{http_code}\n\n"
  sleep 1
done
```

Expected: First 10 requests succeed (or return 401), requests 11-15 return 429.

---

## Python Testing Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Register
response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "python@example.com",
        "password": "Python123!@#",
        "full_name": "Python User",
        "organization_name": "Python Org"
    }
)
print(f"Register: {response.status_code}")
tokens = response.json()

# Get current user
response = requests.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": f"Bearer {tokens['access_token']}"}
)
print(f"Get user: {response.status_code}")
print(response.json())

# Refresh token
response = requests.post(
    f"{BASE_URL}/auth/refresh",
    json={"refresh_token": tokens["refresh_token"]}
)
print(f"Refresh: {response.status_code}")
new_tokens = response.json()
```

---

## Common Errors

### 401 Unauthorized
- Invalid credentials
- Expired token
- Malformed token
- Missing Authorization header

### 403 Forbidden
- Account inactive
- Email not verified (for protected endpoints)
- Insufficient permissions

### 422 Validation Error
- Invalid email format
- Weak password
- Missing required fields
- Invalid field types

### 429 Too Many Requests
- Rate limit exceeded
- Check `Retry-After` header
- Wait before retrying

---

## Security Notes

1. **Always use HTTPS in production**
2. **Store tokens securely** (HttpOnly cookies or secure storage)
3. **Never log or expose tokens**
4. **Rotate tokens regularly**
5. **Monitor for suspicious activity**
6. **Use strong passwords**
7. **Enable email verification**
