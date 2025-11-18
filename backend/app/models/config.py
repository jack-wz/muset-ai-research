"""Configuration models for models, MCP servers, and skills."""
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import BaseMixin


class ModelConfig(Base, BaseMixin):
    """Model configuration."""

    __tablename__ = "model_configs"

    provider = Column(String, nullable=False)  # anthropic, openai, azure, local
    label = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    api_key_secret_id = Column(String, nullable=True)  # Reference to encrypted storage
    base_url = Column(String, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)

    # Capabilities
    capabilities = Column(
        JSONB,
        nullable=False,
        default={
            "streaming": True,
            "vision": False,
            "toolUse": True,
            "multilingual": True,
        },
    )

    # Guardrails
    guardrails = Column(JSONB, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ModelConfig {self.provider}/{self.model_name}>"


class MCPServerConfig(Base, BaseMixin):
    """MCP server configuration."""

    __tablename__ = "mcp_server_configs"

    name = Column(String, nullable=False, unique=True)
    endpoint = Column(String, nullable=False)
    protocol = Column(String, default="http", nullable=False)  # http, ws
    auth_type = Column(String, default="none", nullable=False)  # none, api_key, oauth
    auth_secret_id = Column(String, nullable=True)
    status = Column(
        String,
        default="disconnected",
        nullable=False,
    )  # disconnected, connected, error
    last_connected_at = Column(DateTime(timezone=True), nullable=True)

    # Tools and retry policy
    tools = Column(JSONB, default=[], nullable=False)
    retry_policy = Column(
        JSONB,
        nullable=False,
        default={"maxAttempts": 3, "backoffMs": 1000},
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<MCPServerConfig {self.name}>"


class SkillPackage(Base, BaseMixin):
    """Skill package configuration."""

    __tablename__ = "skill_packages"

    name = Column(String, nullable=False, unique=True)
    version = Column(String, nullable=False)
    provider = Column(String, default="claude", nullable=False)  # claude, custom
    manifest_path = Column(String, nullable=False)  # Path to SKILL.md
    instructions = Column(Text, nullable=False)
    default_enabled = Column(Boolean, default=False, nullable=False)

    # Resources and tools
    required_resources = Column(JSONB, default=[], nullable=False)
    exposed_tools = Column(JSONB, default=[], nullable=False)

    # Sandbox policy
    sandbox_policy = Column(
        JSONB,
        nullable=False,
        default={
            "allowNetwork": False,
            "allowedHosts": [],
            "memoryLimitMB": 256,
            "timeoutMs": 30000,
        },
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<SkillPackage {self.name} v{self.version}>"
