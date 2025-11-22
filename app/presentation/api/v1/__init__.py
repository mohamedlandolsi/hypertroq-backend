"""API v1 router configuration."""
from fastapi import APIRouter

from app.presentation.api.v1 import auth, users, health, exercises

api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(exercises.router)
