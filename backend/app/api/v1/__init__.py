"""API v1 router."""
from fastapi import APIRouter

from app.api.v1 import auth, users

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
