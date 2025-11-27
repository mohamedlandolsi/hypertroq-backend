"""Authentication routes."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.application.dtos.auth_dto import (
    TokenDTO,
    TokenRefreshDTO,
    LoginDTO,
    PasswordResetRequestDTO,
    PasswordResetConfirmDTO,
    EmailVerificationDTO,
)
from app.application.dtos.organization_dto import OrganizationCreateDTO
from app.application.dtos.user_dto import UserCreateDTO, UserResponseDTO, MessageResponseDTO
from app.application.services.auth_service import AuthService
from app.application.services.organization_service import OrganizationService
from app.application.services.user_service import UserService
from app.infrastructure.repositories.organization_repository import OrganizationRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.core.dependencies import DatabaseDep, CurrentUserDep

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_user_service(db: DatabaseDep) -> UserService:
    """Get user service dependency."""
    user_repo = UserRepository(db)
    return UserService(user_repo)


def get_auth_service(user_service: Annotated[UserService, Depends(get_user_service)]) -> AuthService:
    """Get auth service dependency."""
    return AuthService(user_service)


def get_organization_service(db: DatabaseDep) -> OrganizationService:
    """Get organization service dependency."""
    org_repo = OrganizationRepository(db)
    user_repo = UserRepository(db)
    return OrganizationService(org_repo, user_repo)


@router.post("/register", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreateDTO,
    user_service: Annotated[UserService, Depends(get_user_service)],
    organization_service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> UserResponseDTO:
    """Register a new user and organization when needed."""
    organization_id = user_data.organization_id

    if organization_id is None:
        # Create a new organization when only organization_name is provided
        organization = await organization_service.create_organization(
            OrganizationCreateDTO(name=user_data.organization_name)
        )
        organization_id = organization.id

    user_payload = UserCreateDTO(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        organization_id=organization_id,
    )

    return await user_service.create_user(user_payload)


@router.post("/login", response_model=TokenDTO)
async def login(
    login_data: LoginDTO,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> TokenDTO:
    """Login and get access token."""
    return await auth_service.login(login_data)


@router.post("/login/form", response_model=TokenDTO)
async def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> TokenDTO:
    """Login with form data (for OAuth2 compatibility)."""
    login_data = LoginDTO(email=form_data.username, password=form_data.password)
    return await auth_service.login(login_data)


@router.post("/refresh", response_model=TokenDTO)
async def refresh_token(
    token_data: TokenRefreshDTO,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> TokenDTO:
    """Refresh access token."""
    return await auth_service.refresh_token(token_data.refresh_token)


@router.get("/me", response_model=UserResponseDTO)
async def get_current_user(
    current_user: CurrentUserDep,
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> UserResponseDTO:
    """Get current authenticated user details."""
    user = await user_service.get_user(current_user.id)
    return user


@router.post("/password-reset/request", response_model=MessageResponseDTO)
async def request_password_reset(
    request_data: PasswordResetRequestDTO,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> MessageResponseDTO:
    """Request password reset email."""
    await auth_service.request_password_reset(request_data.email)
    # Always return success to prevent email enumeration
    return MessageResponseDTO(
        message="If an account exists with this email, a password reset link has been sent."
    )


@router.post("/password-reset/confirm", response_model=MessageResponseDTO)
async def confirm_password_reset(
    reset_data: PasswordResetConfirmDTO,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> MessageResponseDTO:
    """Confirm password reset with token."""
    await auth_service.confirm_password_reset(reset_data.token, reset_data.new_password)
    return MessageResponseDTO(message="Password has been reset successfully.")


@router.post("/verify-email/{token}", response_model=EmailVerificationDTO)
async def verify_email(
    token: str,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> EmailVerificationDTO:
    """Verify user email with token."""
    result = await auth_service.verify_email(token)
    return EmailVerificationDTO(
        message="Email verified successfully.",
        email_verified=result
    )
