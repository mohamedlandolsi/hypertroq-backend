# User Profile API Reference

## Overview

User profile endpoints for managing user accounts, profile information, organization details, and activity tracking.

**Base Path**: `/api/v1/users`  
**Authentication**: Required (Bearer token) for all endpoints

---

## Endpoints

### 1. Get Current User Profile

Retrieve the authenticated user's complete profile including organization and subscription details.

```http
GET /api/v1/users/me
```

**Authentication**: Required

**Response**: `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "organization_id": "660e8400-e29b-41d4-a716-446655440000",
  "role": "USER",
  "is_active": true,
  "is_verified": true,
  "profile_image_url": "https://storage.googleapis.com/hypertroq-user-uploads/users/550e8400-e29b-41d4-a716-446655440000/profile.jpg",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T14:45:00Z",
  "organization": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "FitnessPro Gym",
    "subscription_tier": "PRO",
    "subscription_status": "ACTIVE",
    "lemonsqueezy_customer_id": "123456",
    "lemonsqueezy_subscription_id": "sub_789012",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Use Cases**:
- Display user profile in UI
- Show subscription status
- Check user verification status
- Display organization name

---

### 2. Update User Profile

Update user profile information (name only).

```http
PUT /api/v1/users/me
Content-Type: application/json
```

**Authentication**: Required

**Request Body**:

```json
{
  "full_name": "John Smith"
}
```

**Fields**:
- `full_name` (string, optional): User's full name (1-255 characters)

**Response**: `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "full_name": "John Smith",
  "organization_id": "660e8400-e29b-41d4-a716-446655440000",
  "role": "USER",
  "is_active": true,
  "is_verified": true,
  "profile_image_url": "https://storage.googleapis.com/.../profile.jpg",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:00:00Z"
}
```

**Error Responses**:

```json
// 401 Unauthorized
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}

// 422 Validation Error
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "loc": ["body", "full_name"],
        "msg": "ensure this value has at least 1 characters",
        "type": "value_error.any_str.min_length"
      }
    ]
  }
}
```

---

### 3. Upload Profile Image

Upload a new profile image to cloud storage.

```http
PUT /api/v1/users/me/image
Content-Type: multipart/form-data
```

**Authentication**: Required

**Request Body** (multipart/form-data):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| image | file | Yes | Image file (JPEG, PNG, or WebP) |

**File Requirements**:
- **Formats**: JPEG, PNG, WebP
- **Maximum Size**: 5 MB
- **Recommended**: Square aspect ratio (1:1), minimum 200x200 pixels

**Response**: `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "organization_id": "660e8400-e29b-41d4-a716-446655440000",
  "role": "USER",
  "is_active": true,
  "is_verified": true,
  "profile_image_url": "https://storage.googleapis.com/hypertroq-user-uploads/users/550e8400-e29b-41d4-a716-446655440000/profile.jpg",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:30:00Z"
}
```

**cURL Example**:

```bash
curl -X PUT "https://api.hypertroq.com/api/v1/users/me/image" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "image=@/path/to/profile.jpg"
```

**JavaScript Example**:

```javascript
const formData = new FormData();
formData.append('image', fileInput.files[0]);

const response = await fetch('/api/v1/users/me/image', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});

const updatedUser = await response.json();
```

**Error Responses**:

```json
// 400 Bad Request - Invalid file type
{
  "detail": "Invalid file type. Allowed types: image/jpeg, image/png, image/webp"
}

// 400 Bad Request - File too large
{
  "detail": "File too large. Maximum size: 5 MB"
}

// 500 Internal Server Error - Upload failed
{
  "detail": "Failed to upload image"
}
```

**Image Storage**:
- Bucket: `hypertroq-user-uploads`
- Path: `users/{user_id}/profile.{extension}`
- Access: Public URL (no authentication required for viewing)
- Old images: Automatically overwritten

---

### 4. Change Password

Change user password with current password verification.

```http
PUT /api/v1/users/me/password
Content-Type: application/json
```

**Authentication**: Required

**Request Body**:

```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePass456!"
}
```

**Fields**:
- `current_password` (string, required): Current password (minimum 8 characters)
- `new_password` (string, required): New password (minimum 8 characters)

**Password Requirements**:
- Minimum 8 characters
- Recommended: Mix of uppercase, lowercase, numbers, and special characters

**Response**: `200 OK`

```json
{
  "message": "Password changed successfully"
}
```

**Error Responses**:

```json
// 400 Bad Request - Incorrect current password
{
  "detail": "Current password is incorrect"
}

// 404 Not Found - User not found
{
  "detail": "User not found"
}

// 422 Validation Error - Password too short
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "loc": ["body", "new_password"],
        "msg": "ensure this value has at least 8 characters",
        "type": "value_error.any_str.min_length"
      }
    ]
  }
}
```

**Best Practices**:
- Prompt user to re-login after password change
- Clear all active sessions/tokens
- Send confirmation email
- Log password change event for security audit

---

### 5. Get User's Organization

Retrieve detailed organization information including team members and subscription status.

```http
GET /api/v1/users/me/organization
```

**Authentication**: Required

**Response**: `200 OK`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "FitnessPro Gym",
  "subscription_tier": "PRO",
  "subscription_status": "ACTIVE",
  "lemonsqueezy_customer_id": "123456",
  "lemonsqueezy_subscription_id": "sub_789012",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "user_count": 15,
  "can_create_custom_exercises": true,
  "can_create_programs": true,
  "has_unlimited_ai_queries": true
}
```

**Response Fields**:
- `user_count` (integer): Number of users in organization
- `can_create_custom_exercises` (boolean): PRO feature flag
- `can_create_programs` (boolean): PRO feature flag
- `has_unlimited_ai_queries` (boolean): PRO feature flag

**Use Cases**:
- Display subscription status
- Check feature availability
- Show team member count
- Prompt for upgrade if on FREE tier

**Feature Availability**:

| Feature | FREE Tier | PRO Tier |
|---------|-----------|----------|
| Custom Exercises | ❌ No | ✅ Yes |
| Program Creation | ❌ No | ✅ Yes |
| AI Queries | 10/month | ✅ Unlimited |

---

### 6. Get User's Programs

List all training programs created by the user.

```http
GET /api/v1/users/me/programs?skip=0&limit=20
```

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | integer | 0 | Number of records to skip |
| limit | integer | 20 | Maximum records to return (max: 100) |

**Response**: `200 OK`

```json
{
  "data": [],
  "meta": {
    "total": 0,
    "skip": 0,
    "limit": 20
  },
  "message": "Program integration pending - use /api/v1/programs endpoint"
}
```

**Note**: This endpoint is a placeholder. Use `/api/v1/programs` for full program management.

**Future Response Format**:

```json
{
  "data": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "name": "Push Pull Legs",
      "description": "6-day split for hypertrophy",
      "sessions_count": 3,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-20T14:45:00Z"
    }
  ],
  "meta": {
    "total": 1,
    "skip": 0,
    "limit": 20
  }
}
```

---

### 7. Get User Activity Stats

Retrieve user activity statistics and metrics.

```http
GET /api/v1/users/me/activity
```

**Authentication**: Required

**Response**: `200 OK`

```json
{
  "programs_created": 5,
  "sessions_created": 15,
  "exercises_created": 3,
  "last_active": "2024-01-20T14:45:00Z",
  "account_age_days": 45
}
```

**Response Fields**:
- `programs_created` (integer): Total programs created by user
- `sessions_created` (integer): Total workout sessions created
- `exercises_created` (integer): Total custom exercises created (PRO only)
- `last_active` (datetime): Last activity timestamp
- `account_age_days` (integer): Days since account creation

**Use Cases**:
- Display activity dashboard
- Show user engagement metrics
- Identify inactive users
- Calculate account anniversary

**Note**: Current implementation returns placeholder values (0 for counts). Integration with program/exercise repositories pending.

---

### 8. Request Account Deletion

Initiate account deletion process with grace period.

```http
DELETE /api/v1/users/me
```

**Authentication**: Required

**Response**: `200 OK`

```json
{
  "message": "Account deletion requested. Your account will be deleted after 30 days grace period. Check your email for confirmation link."
}
```

**Account Deletion Process**:

1. **Immediate**: Account marked for deletion
2. **Email Sent**: Confirmation link with cancellation option
3. **Grace Period**: 30 days to cancel deletion
4. **Deletion**: Account and all data permanently removed

**What Gets Deleted**:
- User account and profile
- All created programs and sessions
- Custom exercises (if any)
- Activity history and logs
- Profile images from cloud storage

**What's Preserved**:
- Organization data (if other users exist)
- Global exercise library contributions
- Anonymized analytics data (if applicable)

**Cancellation**:
Users can cancel deletion within 30 days by:
- Clicking cancellation link in email
- Logging in to reactivate account

**Error Response**:

```json
// 404 Not Found
{
  "detail": "User not found"
}
```

**Important Notes**:
- ⚠️ Current implementation deletes immediately (no grace period)
- 🚧 Grace period and email confirmation workflow is TODO
- 💾 Backup critical data before deletion
- 🔒 Deletion is irreversible after grace period

---

## Authentication

All endpoints require Bearer token authentication:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Getting Access Token**:

```bash
curl -X POST "https://api.hypertroq.com/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**Response**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| UNAUTHORIZED | 401 | Missing or invalid authentication token |
| FORBIDDEN | 403 | Insufficient permissions for action |
| NOT_FOUND | 404 | User or resource not found |
| VALIDATION_ERROR | 422 | Invalid request data |
| INTERNAL_SERVER_ERROR | 500 | Unexpected server error |

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| GET /users/me | 100 requests | 1 minute |
| PUT /users/me | 20 requests | 1 minute |
| PUT /users/me/image | 10 requests | 1 hour |
| PUT /users/me/password | 5 requests | 1 hour |
| DELETE /users/me | 1 request | 1 hour |

**Rate Limit Headers**:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642329600
```

---

## Examples

### Complete Profile Update Flow

```javascript
// 1. Get current profile
const profile = await fetch('/api/v1/users/me', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

console.log(`Welcome ${profile.full_name}!`);
console.log(`Subscription: ${profile.organization.subscription_tier}`);

// 2. Update name
const updated = await fetch('/api/v1/users/me', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ full_name: 'New Name' })
}).then(r => r.json());

// 3. Upload profile image
const formData = new FormData();
formData.append('image', imageFile);

const withImage = await fetch('/api/v1/users/me/image', {
  method: 'PUT',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
}).then(r => r.json());

console.log(`Profile image: ${withImage.profile_image_url}`);
```

### Check Feature Access

```javascript
// Get organization details
const org = await fetch('/api/v1/users/me/organization', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Check feature availability
if (!org.can_create_custom_exercises) {
  alert('Upgrade to PRO to create custom exercises!');
  window.location.href = '/pricing';
} else {
  // Allow custom exercise creation
  createCustomExercise();
}
```

### Password Change with Validation

```javascript
async function changePassword(currentPassword, newPassword) {
  // Client-side validation
  if (newPassword.length < 8) {
    throw new Error('Password must be at least 8 characters');
  }
  
  if (newPassword === currentPassword) {
    throw new Error('New password must be different');
  }
  
  // Server request
  const response = await fetch('/api/v1/users/me/password', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Password change failed');
  }
  
  // Clear tokens and redirect to login
  localStorage.removeItem('access_token');
  window.location.href = '/login?message=password_changed';
}
```

---

## Best Practices

### 1. Profile Image Optimization

**Client-Side**:
- Resize images before upload (recommended: 400x400px)
- Compress to reduce file size
- Use modern formats (WebP preferred)
- Show upload progress bar

**Example with canvas**:

```javascript
async function resizeImage(file, maxSize = 400) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      // Calculate dimensions
      let width = img.width;
      let height = img.height;
      
      if (width > height) {
        if (width > maxSize) {
          height *= maxSize / width;
          width = maxSize;
        }
      } else {
        if (height > maxSize) {
          width *= maxSize / height;
          height = maxSize;
        }
      }
      
      canvas.width = width;
      canvas.height = height;
      ctx.drawImage(img, 0, 0, width, height);
      
      canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.9);
    };
    
    img.src = URL.createObjectURL(file);
  });
}

// Usage
const resizedBlob = await resizeImage(fileInput.files[0]);
formData.append('image', resizedBlob, 'profile.jpg');
```

### 2. Secure Password Handling

**Frontend**:
- Never store passwords in localStorage/sessionStorage
- Clear password fields after submission
- Use password strength indicator
- Implement password visibility toggle

**Backend** (handled automatically):
- Passwords hashed with bcrypt
- Salt rounds: 12
- Verification uses constant-time comparison

### 3. Activity Dashboard

```javascript
// Fetch all user data in parallel
const [profile, organization, activity] = await Promise.all([
  fetch('/api/v1/users/me').then(r => r.json()),
  fetch('/api/v1/users/me/organization').then(r => r.json()),
  fetch('/api/v1/users/me/activity').then(r => r.json())
]);

// Display unified dashboard
renderDashboard({
  user: profile,
  org: organization,
  stats: activity
});
```

### 4. Graceful Degradation

```javascript
// Handle missing profile image
const avatarUrl = user.profile_image_url || getDefaultAvatar(user.full_name);

function getDefaultAvatar(name) {
  // Generate avatar with initials
  const initials = name.split(' ').map(n => n[0]).join('');
  return `https://ui-avatars.com/api/?name=${initials}&size=200`;
}
```

---

## Troubleshooting

### Issue: Image upload fails with 500 error

**Possible Causes**:
- Google Cloud Storage credentials not configured
- Bucket permissions incorrect
- Network connectivity issues

**Solution**:
1. Verify `GOOGLE_CLOUD_STORAGE_BUCKET` environment variable
2. Check service account has "Storage Object Creator" role
3. Test bucket access: `gsutil ls gs://hypertroq-user-uploads`

### Issue: Password change fails with "incorrect password"

**Possible Causes**:
- User typing wrong current password
- Password was recently changed
- Account compromised

**Solution**:
1. Verify current password in safe environment
2. Use "Forgot Password" flow if locked out
3. Check for suspicious login activity

### Issue: Organization stats show 0 users

**Possible Causes**:
- No other users in organization
- User repository query failing

**Solution**:
- Check organization members in admin panel
- Verify database connections
- Review logs for errors

---

## Migration Guide

### From v0.x to v1.0

**Breaking Changes**:

1. **Profile update endpoint split**:
   ```javascript
   // Old (v0.x) - Deprecated
   PUT /users/me
   {
     "full_name": "...",
     "profile_image_url": "..."  // Manual URL
   }
   
   // New (v1.0)
   PUT /users/me
   { "full_name": "..." }
   
   PUT /users/me/image
   FormData with file
   ```

2. **Organization details moved**:
   ```javascript
   // Old (v0.x)
   GET /users/me  // Includes organization
   
   // New (v1.0)
   GET /users/me/organization  // Dedicated endpoint
   ```

**Migration Steps**:

1. Update frontend to use separate image upload endpoint
2. Update organization fetching to dedicated endpoint
3. Test all profile update flows
4. Update API documentation links

---

## Support

- **Documentation**: https://docs.hypertroq.com
- **API Status**: https://status.hypertroq.com
- **Support Email**: support@hypertroq.com
- **GitHub Issues**: https://github.com/hypertroq/backend/issues
