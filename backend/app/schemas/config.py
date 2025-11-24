"""Configuration schemas."""
from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Model Configuration Schemas
class ModelConfigBase(BaseModel):
    """Base model configuration schema."""

    provider: Literal["anthropic", "openai", "azure", "local"] = Field(
        description="LLM 提供商"
    )
    label: str = Field(description="配置显示名称")
    model_name: str = Field(description="模型名称")
    base_url: Optional[str] = Field(None, description="自定义 API 端点")
    is_default: bool = Field(False, description="是否为默认模型")
    capabilities: dict[str, bool] = Field(
        default={
            "streaming": True,
            "vision": False,
            "toolUse": True,
            "multilingual": True,
        },
        description="模型能力",
    )
    guardrails: Optional[dict[str, Any]] = Field(None, description="防护栏配置")


class ModelConfigCreate(ModelConfigBase):
    """Model configuration creation schema."""

    api_key: Optional[str] = Field(None, description="API 密钥（加密存储）")


class ModelConfigUpdate(BaseModel):
    """Model configuration update schema."""

    label: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_default: Optional[bool] = None
    capabilities: Optional[dict[str, bool]] = None
    guardrails: Optional[dict[str, Any]] = None


class ModelConfigResponse(ModelConfigBase):
    """Model configuration response schema."""

    id: UUID
    api_key_secret_id: Optional[str] = None  # 不返回实际密钥
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


# MCP Server Configuration Schemas
class MCPServerConfigBase(BaseModel):
    """Base MCP server configuration schema."""

    name: str = Field(description="服务器名称")
    protocol: Literal["stdio", "http", "ws"] = Field(
        "stdio", description="通信协议"
    )
    command: Optional[str] = Field(None, description="启动命令（stdio）")
    args: Optional[list[str]] = Field(None, description="命令参数（stdio）")
    env: Optional[dict[str, str]] = Field(None, description="环境变量")
    endpoint: Optional[str] = Field(None, description="服务端点（http/ws）")
    auth_type: Literal["none", "api_key", "oauth"] = Field(
        "none", description="认证类型"
    )
    auto_reconnect: bool = Field(True, description="自动重连")
    retry_policy: dict[str, int] = Field(
        default={"maxAttempts": 3, "backoffMs": 1000},
        description="重试策略",
    )


class MCPServerConfigCreate(MCPServerConfigBase):
    """MCP server configuration creation schema."""

    auth_secret: Optional[str] = Field(None, description="认证密钥")


class MCPServerConfigUpdate(BaseModel):
    """MCP server configuration update schema."""

    command: Optional[str] = None
    args: Optional[list[str]] = None
    env: Optional[dict[str, str]] = None
    endpoint: Optional[str] = None
    auth_secret: Optional[str] = None
    auto_reconnect: Optional[bool] = None
    retry_policy: Optional[dict[str, int]] = None


class MCPServerConfigResponse(MCPServerConfigBase):
    """MCP server configuration response schema."""

    id: UUID
    status: str
    last_connected_at: Optional[datetime] = None
    tools: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


# Skill Package Schemas
class SkillPackageBase(BaseModel):
    """Base skill package schema."""

    name: str = Field(description="技能包名称")
    version: str = Field(description="版本号")
    provider: Literal["claude", "custom"] = Field("claude", description="提供商")
    instructions: str = Field(description="技能指令")
    default_enabled: bool = Field(False, description="默认启用")
    required_resources: list[dict[str, Any]] = Field(
        default=[], description="所需资源"
    )
    exposed_tools: list[dict[str, Any]] = Field(default=[], description="暴露的工具")
    sandbox_policy: dict[str, Any] = Field(
        default={
            "allowNetwork": False,
            "allowedHosts": [],
            "memoryLimitMB": 256,
            "timeoutMs": 30000,
        },
        description="沙箱策略",
    )


class SkillPackageCreate(SkillPackageBase):
    """Skill package creation schema."""

    manifest_path: str = Field(description="SKILL.md 文件路径")


class SkillPackageUpdate(BaseModel):
    """Skill package update schema."""

    instructions: Optional[str] = None
    default_enabled: Optional[bool] = None
    sandbox_policy: Optional[dict[str, Any]] = None


class SkillPackageResponse(SkillPackageBase):
    """Skill package response schema."""

    id: UUID
    manifest_path: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


# Vector Database Configuration Schemas
class VectorDBConfigBase(BaseModel):
    """Base vector database configuration schema."""

    provider: Literal["pinecone", "faiss", "weaviate"] = Field(
        "pinecone", description="向量数据库提供商"
    )
    index_name: str = Field(description="索引名称")
    environment: Optional[str] = Field(None, description="环境（Pinecone）")
    dimension: int = Field(1536, description="向量维度")
    metric: Literal["cosine", "euclidean", "dotproduct"] = Field(
        "cosine", description="距离度量"
    )


class VectorDBConfigCreate(VectorDBConfigBase):
    """Vector database configuration creation schema."""

    api_key: Optional[str] = Field(None, description="API 密钥")


class VectorDBConfigUpdate(BaseModel):
    """Vector database configuration update schema."""

    api_key: Optional[str] = None
    index_name: Optional[str] = None
    environment: Optional[str] = None


class VectorDBConfigResponse(VectorDBConfigBase):
    """Vector database configuration response schema."""

    id: UUID
    status: str  # connected, disconnected, error
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


# Connection Test Schemas
class ConnectionTestRequest(BaseModel):
    """Connection test request schema."""

    config_type: Literal["model", "mcp", "vector_db"]
    config_id: UUID


class ConnectionTestResponse(BaseModel):
    """Connection test response schema."""

    success: bool
    message: str
    latency_ms: Optional[float] = None
    details: Optional[dict[str, Any]] = None


# Configuration Export/Import Schemas
class ConfigExportResponse(BaseModel):
    """Configuration export response schema."""

    models: list[ModelConfigResponse]
    mcp_servers: list[MCPServerConfigResponse]
    skills: list[SkillPackageResponse]
    vector_db: Optional[VectorDBConfigResponse] = None
    exported_at: datetime


class ConfigImportRequest(BaseModel):
    """Configuration import request schema."""

    models: Optional[list[ModelConfigCreate]] = None
    mcp_servers: Optional[list[MCPServerConfigCreate]] = None
    skills: Optional[list[SkillPackageCreate]] = None
    vector_db: Optional[VectorDBConfigCreate] = None
    merge_strategy: Literal["replace", "merge", "skip"] = Field(
        "merge", description="导入策略"
    )


class ConfigImportResponse(BaseModel):
    """Configuration import response schema."""

    success: bool
    imported_models: int = 0
    imported_mcp_servers: int = 0
    imported_skills: int = 0
    errors: list[str] = []
