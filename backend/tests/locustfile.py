"""Locust load testing configuration."""
import json
import random
from locust import HttpUser, between, task


class MusetUser(HttpUser):
    """Simulate Muset application user."""

    wait_time = between(1, 5)  # Wait 1-5 seconds between requests
    host = "http://localhost:7989"

    def on_start(self):
        """Initialize user session."""
        # Register/login user
        self.register_user()
        self.login()

    def register_user(self):
        """Register a new user."""
        email = f"test_{random.randint(1000, 9999)}@example.com"
        password = "TestPassword123"

        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Test User",
            },
            name="/api/v1/auth/register",
        )

        if response.status_code == 200:
            self.email = email
            self.password = password
        elif response.status_code == 409:
            # User already exists, use existing credentials
            self.email = email
            self.password = password

    def login(self):
        """Login user."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": self.email,
                "password": self.password,
            },
            name="/api/v1/auth/login",
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}

    @task(3)
    def get_health(self):
        """Get health status."""
        self.client.get("/health", name="/health")

    @task(5)
    def get_workspaces(self):
        """Get user workspaces."""
        if hasattr(self, "headers"):
            self.client.get(
                "/api/v1/workspaces",
                headers=self.headers,
                name="/api/v1/workspaces",
            )

    @task(4)
    def create_workspace(self):
        """Create a new workspace."""
        if hasattr(self, "headers"):
            response = self.client.post(
                "/api/v1/workspaces",
                headers=self.headers,
                json={
                    "name": f"Test Workspace {random.randint(1, 1000)}",
                    "description": "Test workspace for load testing",
                },
                name="/api/v1/workspaces [POST]",
            )

            if response.status_code == 200:
                data = response.json()
                self.workspace_id = data.get("id")

    @task(3)
    def get_workspace_pages(self):
        """Get workspace pages."""
        if hasattr(self, "headers") and hasattr(self, "workspace_id"):
            self.client.get(
                f"/api/v1/workspaces/{self.workspace_id}/pages",
                headers=self.headers,
                name="/api/v1/workspaces/{id}/pages",
            )

    @task(4)
    def create_page(self):
        """Create a new page."""
        if hasattr(self, "headers") and hasattr(self, "workspace_id"):
            response = self.client.post(
                "/api/v1/pages",
                headers=self.headers,
                json={
                    "workspace_id": self.workspace_id,
                    "title": f"Test Page {random.randint(1, 1000)}",
                    "content": "This is test content for load testing.",
                },
                name="/api/v1/pages [POST]",
            )

            if response.status_code == 200:
                data = response.json()
                self.page_id = data.get("id")

    @task(2)
    def update_page(self):
        """Update a page."""
        if hasattr(self, "headers") and hasattr(self, "page_id"):
            self.client.put(
                f"/api/v1/pages/{self.page_id}",
                headers=self.headers,
                json={
                    "title": f"Updated Page {random.randint(1, 1000)}",
                    "content": "This is updated content for load testing.",
                },
                name="/api/v1/pages/{id} [PUT]",
            )

    @task(1)
    def get_skills(self):
        """Get available skills."""
        if hasattr(self, "headers"):
            self.client.get(
                "/api/v1/skills",
                headers=self.headers,
                name="/api/v1/skills",
            )

    @task(1)
    def get_models(self):
        """Get available models."""
        if hasattr(self, "headers"):
            self.client.get(
                "/api/v1/models",
                headers=self.headers,
                name="/api/v1/models",
            )


class HighLoadUser(HttpUser):
    """Simulate high-load scenarios."""

    wait_time = between(0.1, 0.5)  # Very short wait time
    host = "http://localhost:7989"

    @task(10)
    def rapid_health_checks(self):
        """Rapid health check requests."""
        self.client.get("/health", name="/health [rapid]")

    @task(5)
    def rapid_api_calls(self):
        """Rapid API calls."""
        self.client.get("/api/v1/health", name="/api/v1/health [rapid]")


class StressTestUser(HttpUser):
    """Simulate stress test scenarios."""

    wait_time = between(0, 1)
    host = "http://localhost:7989"

    def on_start(self):
        """Initialize user session."""
        self.register_user()
        self.login()

    def register_user(self):
        """Register a new user."""
        email = f"stress_{random.randint(1000, 99999)}@example.com"
        password = "TestPassword123"

        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Stress Test User",
            },
            name="/api/v1/auth/register [stress]",
        )

        if response.status_code == 200:
            self.email = email
            self.password = password
        elif response.status_code == 409:
            self.email = email
            self.password = password

    def login(self):
        """Login user."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": self.email,
                "password": self.password,
            },
            name="/api/v1/auth/login [stress]",
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}

    @task
    def create_multiple_workspaces(self):
        """Create multiple workspaces rapidly."""
        if hasattr(self, "headers"):
            for i in range(5):
                self.client.post(
                    "/api/v1/workspaces",
                    headers=self.headers,
                    json={
                        "name": f"Stress Workspace {random.randint(1, 10000)}",
                        "description": "Stress test workspace",
                    },
                    name="/api/v1/workspaces [POST stress]",
                )
