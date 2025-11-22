"""Authentication routes."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.application.dtos.auth_dto import TokenDTO, TokenRefreshDTO, LoginDTO
from app.application.dtos.user_dto import UserCreateDTO, UserResponseDTO
from app.application.services.auth_service import AuthService
from app.application.services.user_service import UserService
from app.infrastructure.repositories.user_repository import UserRepository
from app.core.dependencies import DatabaseDep

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_user_service(db: DatabaseDep) -> UserService:
    """Get user service dependency."""
    user_repo = UserRepository(db)
    return UserService(user_repo)


def get_auth_service(user_service: Annotated[UserService, Depends(get_user_service)]) -> AuthService:
    """Get auth service dependency."""
    return AuthService(user_service)


@router.post("/register", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreateDTO,
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> UserResponseDTO:
    """Register a new user."""
    return await user_service.create_user(user_data)


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
