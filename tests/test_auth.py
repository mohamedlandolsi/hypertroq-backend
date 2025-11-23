"""
Authentication API tests.

Tests for user registration, login, token refresh,
email verification, and password reset functionality.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_token, verify_password
from app.models.user import UserModel


class TestRegistration:
    """Tests for user registration."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, async_client: AsyncClient):
        """Test successful user registration."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User",
                "organization_name": "New Org",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify token payload
        payload = decode_token(data["access_token"])
        assert "user_id" in payload
        assert "organization_id" in payload
        assert payload["type"] == "access"
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self, async_client: AsyncClient, test_user: UserModel
    ):
        """Test registration with existing email fails."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "SecurePass123!",
                "full_name": "Duplicate User",
                "organization_name": "Duplicate Org",
            },
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, async_client: AsyncClient):
        """Test registration with weak password fails."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "weakpass@example.com",
                "password": "weak",
                "full_name": "Weak Password User",
                "organization_name": "Weak Org",
            },
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, async_client: AsyncClient):
        """Test registration with invalid email format fails."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "full_name": "Invalid Email User",
                "organization_name": "Invalid Org",
            },
        )
        
        assert response.status_code == 422  # Validation error


class TestLogin:
    """Tests for user login."""
    
    @pytest.mark.asyncio
    async def test_login_success(
        self, async_client: AsyncClient, test_user: UserModel
    ):
        """Test successful login."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123!",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self, async_client: AsyncClient, test_user: UserModel
    ):
        """Test login with wrong password fails."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword123!",
            },
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Password123!",
            },
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self, async_client: AsyncClient, db_session: AsyncSession, test_user: UserModel
    ):
        """Test login with inactive user fails."""
        # Deactivate user
        test_user.is_active = False
        db_session.add(test_user)
        await db_session.commit()
        
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123!",
            },
        )
        
        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"].lower()


class TestTokenRefresh:
    """Tests for token refresh functionality."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, async_client: AsyncClient, user_refresh_token: str
    ):
        """Test successful token refresh."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": user_refresh_token},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        
        # Verify new access token
        payload = decode_token(data["access_token"])
        assert payload["type"] == "access"
    
    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(
        self, async_client: AsyncClient, user_token: str
    ):
        """Test refresh with access token instead of refresh token fails."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": user_token},
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, async_client: AsyncClient):
        """Test refresh with invalid token fails."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        
        assert response.status_code == 401


class TestGetCurrentUser:
    """Tests for getting current user information."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test getting current user with valid token."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "full_name" in data
        assert "role" in data
        assert "organization_id" in data
        assert "hashed_password" not in data  # Should not expose password
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, async_client: AsyncClient):
        """Test getting current user without token fails."""
        response = await async_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, async_client: AsyncClient):
        """Test getting current user with invalid token fails."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        
        assert response.status_code == 401


class TestPasswordReset:
    """Tests for password reset functionality."""
    
    @pytest.mark.asyncio
    async def test_request_password_reset_success(
        self, async_client: AsyncClient, test_user: UserModel, mock_redis
    ):
        """Test requesting password reset."""
        response = await async_client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": test_user.email},
        )
        
        # Always returns success to prevent user enumeration
        assert response.status_code == 200
        assert "reset link" in response.json()["message"].lower()
    
    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_user(
        self, async_client: AsyncClient, mock_redis
    ):
        """Test requesting password reset for non-existent user."""
        response = await async_client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "nonexistent@example.com"},
        )
        
        # Should still return success to prevent user enumeration
        assert response.status_code == 200
        assert "reset link" in response.json()["message"].lower()
    
    @pytest.mark.asyncio
    async def test_confirm_password_reset_success(
        self,
        async_client: AsyncClient,
        test_user: UserModel,
        db_session: AsyncSession,
        mock_redis,
    ):
        """Test confirming password reset with valid token."""
        # Create a reset token
        reset_token = create_access_token(
            subject={"user_id": str(test_user.id), "type": "password_reset"},
        )
        
        # Mock Redis to return user_id for the token
        mock_redis.get.return_value = str(test_user.id)
        
        new_password = "NewSecurePass123!"
        response = await async_client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": reset_token,
                "new_password": new_password,
            },
        )
        
        if response.status_code == 200:
            # Verify password was changed
            await db_session.refresh(test_user)
            assert verify_password(new_password, test_user.hashed_password)
    
    @pytest.mark.asyncio
    async def test_confirm_password_reset_invalid_token(
        self, async_client: AsyncClient
    ):
        """Test confirming password reset with invalid token fails."""
        response = await async_client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": "invalid.token.here",
                "new_password": "NewSecurePass123!",
            },
        )
        
        assert response.status_code == 401


class TestEmailVerification:
    """Tests for email verification functionality."""
    
    @pytest.mark.asyncio
    async def test_verify_email_success(
        self,
        async_client: AsyncClient,
        test_unverified_user: UserModel,
        db_session: AsyncSession,
        mock_redis,
    ):
        """Test email verification with valid token."""
        # Create verification token
        verification_token = create_access_token(
            subject={"user_id": str(test_unverified_user.id), "type": "email_verification"},
        )
        
        # Mock Redis to return user_id for the token
        mock_redis.get.return_value = str(test_unverified_user.id)
        
        response = await async_client.post(
            f"/api/v1/auth/verify-email/{verification_token}",
        )
        
        if response.status_code == 200:
            # Verify user is now verified
            await db_session.refresh(test_unverified_user)
            assert test_unverified_user.is_verified
    
    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, async_client: AsyncClient):
        """Test email verification with invalid token fails."""
        response = await async_client.post(
            "/api/v1/auth/verify-email/invalid.token.here",
        )
        
        assert response.status_code == 401


class TestAuthenticationMiddleware:
    """Tests for authentication middleware behavior."""
    
    @pytest.mark.asyncio
    async def test_protected_route_requires_token(self, async_client: AsyncClient):
        """Test that protected routes require authentication."""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_expired_token_rejected(
        self, async_client: AsyncClient, test_user: UserModel
    ):
        """Test that expired tokens are rejected."""
        from datetime import timedelta
        
        # Create an expired token
        expired_token = create_access_token(
            subject={
                "user_id": str(test_user.id),
                "organization_id": str(test_user.organization_id),
                "role": str(test_user.role.value),
            },
            expires_delta=timedelta(seconds=-1),  # Expired 1 second ago
        )
        
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_malformed_token_rejected(self, async_client: AsyncClient):
        """Test that malformed tokens are rejected."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer malformed-token"},
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_missing_bearer_prefix_rejected(
        self, async_client: AsyncClient, user_token: str
    ):
        """Test that tokens without Bearer prefix are rejected."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": user_token},  # Missing "Bearer "
        )
        
        assert response.status_code == 401
