"""API v1 router."""
from fastapi import APIRouter

# Temporarily disable MCP features due to missing dependencies
# from app.api.v1 import auth, config, mcp_config, models, pages, skills, users, workspaces
from app.api.v1 import auth, models, pages, skills, users, workspaces

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(pages.router, prefix="/workspaces/{workspace_id}/projects", tags=["pages"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
# Temporarily disabled due to missing langchain_mcp dependency
# api_router.include_router(mcp_config.router, prefix="/mcp", tags=["mcp"])
# api_router.include_router(config.router, prefix="/config", tags=["config"])
