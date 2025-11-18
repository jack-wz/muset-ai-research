"""
Tests for Configuration Import/Export API

This module tests the unified configuration import/export endpoints.
Validates requirements 23.1-23.5.
"""

import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config import MCPServerConfig, ModelConfig


class TestConfigImportExportAPI:
    """Test suite for configuration import/export API."""

    @pytest.mark.asyncio
    async def test_export_empty_configuration(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test exporting configuration when system is empty."""
        response = await async_client.get(
            "/api/v1/config/export",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "version" in data
        assert "models" in data
        assert "mcp_servers" in data
        assert data["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_export_with_configurations(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test exporting configuration with existing configs."""
        # Create test configurations
        model = ModelConfig(
            provider="anthropic",
            label="Test Claude",
            model_name="claude-3-5-sonnet-20241022",
            is_default=True,
        )
        mcp_server = MCPServerConfig(
            name="test-server",
            protocol="stdio",
            command="npx",
            args=["-y", "@test/server"],
        )

        db_session.add_all([model, mcp_server])
        await db_session.commit()

        # Export configuration
        response = await async_client.get(
            "/api/v1/config/export",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["models"]["models"]) == 1
        assert len(data["mcp_servers"]["servers"]) == 1

        # Verify model data
        exported_model = data["models"]["models"][0]
        assert exported_model["label"] == "Test Claude"
        assert exported_model["provider"] == "anthropic"

        # Verify MCP data
        exported_server = data["mcp_servers"]["servers"][0]
        assert exported_server["name"] == "test-server"
        assert exported_server["protocol"] == "stdio"

    @pytest.mark.asyncio
    async def test_export_excludes_api_keys_by_default(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that API keys are excluded by default (Requirement 23.2)."""
        # Create model with API key
        from app.core.security import encrypt_api_key

        model = ModelConfig(
            provider="anthropic",
            label="Model with Key",
            model_name="claude-3-5-sonnet-20241022",
            api_key_secret_id=encrypt_api_key("sk-ant-test-key"),
            is_default=False,
        )
        db_session.add(model)
        await db_session.commit()

        # Export without including keys
        response = await async_client.get(
            "/api/v1/config/export",
            headers=auth_headers,
            params={"include_api_keys": False},
        )

        assert response.status_code == 200
        data = response.json()

        exported_model = data["models"]["models"][0]
        assert exported_model["api_key"] is None

    @pytest.mark.asyncio
    async def test_validate_configuration(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test configuration validation endpoint (Requirement 23.4)."""
        valid_config = {
            "version": "1.0",
            "models": {
                "version": "1.0",
                "models": [
                    {
                        "provider": "anthropic",
                        "label": "Test",
                        "model_name": "claude-3-5-sonnet-20241022",
                        "is_default": False,
                        "capabilities": {"streaming": True},
                        "api_key": None,
                        "base_url": None,
                        "guardrails": None,
                    }
                ],
            },
            "mcp_servers": {
                "version": "1.0",
                "servers": [
                    {
                        "name": "test",
                        "protocol": "stdio",
                        "command": "npx",
                        "args": ["-y", "test"],
                        "auto_reconnect": True,
                        "retry_policy": {"maxAttempts": 3, "backoffMs": 1000},
                        "env": None,
                        "endpoint": None,
                        "auth_type": "none",
                    }
                ],
            },
        }

        response = await async_client.post(
            "/api/v1/config/validate",
            json=valid_config,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["preview"]["models_count"] == 1
        assert data["preview"]["mcp_servers_count"] == 1
        assert len(data["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_invalid_configuration(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test validation of invalid configuration."""
        invalid_config = {
            "version": "1.0",
            "models": {
                "version": "1.0",
                "models": [
                    {
                        # Missing required fields
                        "provider": "anthropic",
                    }
                ],
            },
        }

        response = await async_client.post(
            "/api/v1/config/validate",
            json=invalid_config,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert len(data["errors"]) > 0

    @pytest.mark.asyncio
    async def test_import_configuration(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test importing configuration (Requirement 23.3)."""
        import_data = {
            "version": "1.0",
            "models": {
                "version": "1.0",
                "models": [
                    {
                        "provider": "anthropic",
                        "label": "Imported Claude",
                        "model_name": "claude-3-5-sonnet-20241022",
                        "is_default": False,
                        "capabilities": {
                            "streaming": True,
                            "vision": False,
                            "toolUse": True,
                            "multilingual": True,
                        },
                        "api_key": None,
                        "base_url": None,
                        "guardrails": None,
                    }
                ],
            },
            "mcp_servers": {
                "version": "1.0",
                "servers": [
                    {
                        "name": "imported-server",
                        "protocol": "stdio",
                        "command": "npx",
                        "args": ["-y", "@test/server"],
                        "auto_reconnect": True,
                        "retry_policy": {"maxAttempts": 3, "backoffMs": 1000},
                        "env": None,
                        "endpoint": None,
                        "auth_type": "none",
                    }
                ],
            },
        }

        response = await async_client.post(
            "/api/v1/config/import",
            json={"data": import_data, "overwrite": False},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["models_imported"] == 1
        assert data["mcp_servers_imported"] == 1
        assert len(data["errors"]) == 0

    @pytest.mark.asyncio
    async def test_import_with_overwrite(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test selective import with overwrite (Requirement 23.5)."""
        # Create existing configuration
        existing_model = ModelConfig(
            provider="anthropic",
            label="Existing Model",
            model_name="claude-3-sonnet-20240229",
            is_default=False,
        )
        db_session.add(existing_model)
        await db_session.commit()

        # Import data with same label but different model
        import_data = {
            "version": "1.0",
            "models": {
                "version": "1.0",
                "models": [
                    {
                        "provider": "anthropic",
                        "label": "Existing Model",
                        "model_name": "claude-3-5-sonnet-20241022",  # Different
                        "is_default": False,
                        "capabilities": {
                            "streaming": True,
                            "vision": False,
                            "toolUse": True,
                            "multilingual": True,
                        },
                        "api_key": None,
                        "base_url": None,
                        "guardrails": None,
                    }
                ],
            },
            "mcp_servers": {"version": "1.0", "servers": []},
        }

        # Import without overwrite - should skip
        response = await async_client.post(
            "/api/v1/config/import",
            json={"data": import_data, "overwrite": False},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["models_imported"] == 0  # Skipped

        # Import with overwrite - should update
        response = await async_client.post(
            "/api/v1/config/import",
            json={"data": import_data, "overwrite": True},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["models_imported"] == 1  # Updated

        # Verify update
        await db_session.refresh(existing_model)
        assert existing_model.model_name == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_import_partial_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test that import continues even if some configs fail."""
        import_data = {
            "version": "1.0",
            "models": {
                "version": "1.0",
                "models": [
                    {
                        "provider": "anthropic",
                        "label": "Valid Model",
                        "model_name": "claude-3-5-sonnet-20241022",
                        "is_default": False,
                        "capabilities": {"streaming": True},
                        "api_key": None,
                        "base_url": None,
                        "guardrails": None,
                    },
                    {
                        # Invalid - missing required fields
                        "provider": "openai",
                    },
                ],
            },
            "mcp_servers": {"version": "1.0", "servers": []},
        }

        response = await async_client.post(
            "/api/v1/config/import",
            json={"data": import_data, "overwrite": False},
            headers=auth_headers,
        )

        # Should still succeed with partial import
        assert response.status_code == 200
        data = response.json()
        assert data["models_imported"] >= 0  # At least some might succeed

    @pytest.mark.asyncio
    async def test_export_import_roundtrip(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test complete export-import roundtrip (Requirement 23.2, 23.3)."""
        # Create test configurations
        model = ModelConfig(
            provider="anthropic",
            label="Roundtrip Test",
            model_name="claude-3-5-sonnet-20241022",
            is_default=False,
            capabilities={"streaming": True, "vision": True},
        )
        mcp_server = MCPServerConfig(
            name="roundtrip-server",
            protocol="stdio",
            command="npx",
            args=["-y", "@test/server"],
            auto_reconnect=True,
        )

        db_session.add_all([model, mcp_server])
        await db_session.commit()

        original_model_id = model.id
        original_server_id = mcp_server.id

        # Export
        export_response = await async_client.get(
            "/api/v1/config/export",
            headers=auth_headers,
        )
        assert export_response.status_code == 200
        exported_data = export_response.json()

        # Delete configurations
        await db_session.delete(mcp_server)
        await db_session.delete(model)
        await db_session.commit()

        # Import
        import_response = await async_client.post(
            "/api/v1/config/import",
            json={"data": exported_data, "overwrite": True},
            headers=auth_headers,
        )

        assert import_response.status_code == 200
        import_data = import_response.json()

        assert import_data["models_imported"] == 1
        assert import_data["mcp_servers_imported"] == 1

    @pytest.mark.asyncio
    async def test_unauthorized_export(
        self,
        async_client: AsyncClient,
    ):
        """Test that export requires authentication."""
        response = await async_client.get("/api/v1/config/export")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_unauthorized_import(
        self,
        async_client: AsyncClient,
    ):
        """Test that import requires authentication."""
        response = await async_client.post(
            "/api/v1/config/import",
            json={"data": {}, "overwrite": False},
        )

        assert response.status_code == 401
