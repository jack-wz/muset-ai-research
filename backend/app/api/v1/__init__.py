"""API v1 router."""
from fastapi import APIRouter

from app.api.v1 import auth, mcp_config, skills, users

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(mcp_config.router, prefix="/mcp", tags=["mcp"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
