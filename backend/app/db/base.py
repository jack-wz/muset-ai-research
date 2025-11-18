"""Database base configuration and models."""
from sqlalchemy.ext.declarative import declarative_base

# Create declarative base with __allow_unmapped__ for SQLAlchemy 2.0
Base = declarative_base()
Base.__allow_unmapped__ = True

# Import all models here for Alembic migrations
# This ensures all models are registered with Base
from app.models.chat import ChatMessage, ChatSession  # noqa: F401, E402
from app.models.config import MCPServerConfig, ModelConfig, SkillPackage  # noqa: F401, E402
from app.models.file import ContextFile, FileVersion  # noqa: F401, E402
from app.models.memory import Memory  # noqa: F401, E402
from app.models.page import Page  # noqa: F401, E402
from app.models.task import TodoTask, WritingPlan  # noqa: F401, E402
from app.models.user import User  # noqa: F401, E402
from app.models.workspace import Workspace, WorkspaceMember  # noqa: F401, E402
