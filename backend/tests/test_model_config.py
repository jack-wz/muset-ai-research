"""
Tests for Model Configuration API

This module tests the model configuration management endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config import ModelConfig


class TestModelConfigAPI:
    """Test suite for Model Configuration API."""

    @pytest.mark.asyncio
    async def test_list_models_empty(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing models when none exist."""
        response = await async_client.get(
            "/api/v1/models/",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "total" in data
        assert isinstance(data["models"], list)

    @pytest.mark.asyncio
    async def test_create_model_config(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating a model configuration."""
        model_data = {
            "provider": "anthropic",
            "label": "Test Claude",
            "model_name": "claude-3-5-sonnet-20241022",
            "api_key": "test-key-123",
            "is_default": True,
        }

        response = await async_client.post(
            "/api/v1/models/",
            json=model_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == "anthropic"
        assert data["label"] == "Test Claude"
        assert data["model_name"] == "claude-3-5-sonnet-20241022"
        assert data["is_default"] is True
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_model_invalid_provider(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating a model with invalid provider."""
        model_data = {
            "provider": "invalid-provider",
            "label": "Test Model",
            "model_name": "test-model",
        }

        response = await async_client.post(
            "/api/v1/models/",
            json=model_data,
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Invalid provider" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_model_config(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test getting a specific model configuration."""
        # Create a model first
        model = ModelConfig(
            provider="openai",
            label="Test GPT",
            model_name="gpt-4",
            is_default=False,
        )
        db_session.add(model)
        await db_session.commit()
        await db_session.refresh(model)

        # Get the model
        response = await async_client.get(
            f"/api/v1/models/{model.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == model.id
        assert data["provider"] == "openai"
        assert data["label"] == "Test GPT"

    @pytest.mark.asyncio
    async def test_get_nonexistent_model(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting a model that doesn't exist."""
        response = await async_client.get(
            "/api/v1/models/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_model_config(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test updating a model configuration."""
        # Create a model first
        model = ModelConfig(
            provider="anthropic",
            label="Original Label",
            model_name="claude-3-sonnet-20240229",
            is_default=False,
        )
        db_session.add(model)
        await db_session.commit()
        await db_session.refresh(model)

        # Update the model
        update_data = {
            "label": "Updated Label",
            "model_name": "claude-3-5-sonnet-20241022",
        }

        response = await async_client.patch(
            f"/api/v1/models/{model.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "Updated Label"
        assert data["model_name"] == "claude-3-5-sonnet-20241022"
        assert data["provider"] == "anthropic"  # Unchanged

    @pytest.mark.asyncio
    async def test_delete_model_config(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test deleting a model configuration."""
        # Create a model first
        model = ModelConfig(
            provider="openai",
            label="To Delete",
            model_name="gpt-4",
            is_default=False,
        )
        db_session.add(model)
        await db_session.commit()
        await db_session.refresh(model)

        model_id = model.id

        # Delete the model
        response = await async_client.delete(
            f"/api/v1/models/{model_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify it's deleted
        response = await async_client.get(
            f"/api/v1/models/{model_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_default_model(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that deleting default model fails."""
        # Create a default model
        model = ModelConfig(
            provider="anthropic",
            label="Default Model",
            model_name="claude-3-5-sonnet-20241022",
            is_default=True,
        )
        db_session.add(model)
        await db_session.commit()
        await db_session.refresh(model)

        # Try to delete it
        response = await async_client.delete(
            f"/api/v1/models/{model.id}",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Cannot delete default" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_set_default_model(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test setting a model as default."""
        # Create two models
        model1 = ModelConfig(
            provider="anthropic",
            label="Model 1",
            model_name="claude-3-sonnet-20240229",
            is_default=True,
        )
        model2 = ModelConfig(
            provider="anthropic",
            label="Model 2",
            model_name="claude-3-5-sonnet-20241022",
            is_default=False,
        )
        db_session.add_all([model1, model2])
        await db_session.commit()
        await db_session.refresh(model1)
        await db_session.refresh(model2)

        # Set model2 as default
        response = await async_client.post(
            f"/api/v1/models/{model2.id}/set-default",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_default"] is True

        # Verify model1 is no longer default
        await db_session.refresh(model1)
        assert model1.is_default is False

    @pytest.mark.asyncio
    async def test_test_model_connection(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test the model connection test endpoint."""
        # Create a model (will fail since we don't have real API keys)
        model = ModelConfig(
            provider="anthropic",
            label="Test Model",
            model_name="claude-3-5-sonnet-20241022",
            api_key_secret_id="fake-key",
            is_default=False,
        )
        db_session.add(model)
        await db_session.commit()
        await db_session.refresh(model)

        # Test connection (will fail but should return structured response)
        response = await async_client.post(
            f"/api/v1/models/{model.id}/test",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "provider" in data
        assert "model" in data
        assert data["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_list_multiple_models(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test listing multiple models."""
        # Create multiple models
        models = [
            ModelConfig(
                provider="anthropic",
                label="Claude Sonnet",
                model_name="claude-3-5-sonnet-20241022",
                is_default=True,
            ),
            ModelConfig(
                provider="openai",
                label="GPT-4",
                model_name="gpt-4",
                is_default=False,
            ),
            ModelConfig(
                provider="doubao",
                label="豆包",
                model_name="doubao-pro",
                base_url="https://api.doubao.com",
                is_default=False,
            ),
        ]
        db_session.add_all(models)
        await db_session.commit()

        # List all models
        response = await async_client.get(
            "/api/v1/models/",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["models"]) == 3

        # Verify providers
        providers = {m["provider"] for m in data["models"]}
        assert providers == {"anthropic", "openai", "doubao"}

    @pytest.mark.asyncio
    async def test_model_capabilities(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test model capabilities configuration."""
        model_data = {
            "provider": "anthropic",
            "label": "Claude with Vision",
            "model_name": "claude-3-5-sonnet-20241022",
            "capabilities": {
                "streaming": True,
                "vision": True,
                "toolUse": True,
                "multilingual": True,
            },
        }

        response = await async_client.post(
            "/api/v1/models/",
            json=model_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["capabilities"]["vision"] is True
        assert data["capabilities"]["toolUse"] is True
        assert data["capabilities"]["streaming"] is True
        assert data["capabilities"]["multilingual"] is True

    @pytest.mark.asyncio
    async def test_unauthorized_access(
        self,
        async_client: AsyncClient,
    ):
        """Test that unauthorized access is denied."""
        response = await async_client.get("/api/v1/models/")

        assert response.status_code == 401
