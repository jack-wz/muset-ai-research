"""WebSocket manager for real-time notifications."""
import json
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications."""

    def __init__(self):
        """Initialize connection manager."""
        # Map of user_id to list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Connect a WebSocket for a user.

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Disconnect a WebSocket for a user.

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
                # Remove user if no more connections
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            except ValueError:
                pass

    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> None:
        """
        Send message to all connections for a user.

        Args:
            user_id: User ID
            message: Message to send (will be JSON encoded)
        """
        if user_id not in self.active_connections:
            return

        # Get all connections for user
        connections = self.active_connections[user_id].copy()

        # Send to all connections
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection is dead, mark for removal
                disconnected.append(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection, user_id)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast message to all connected users.

        Args:
            message: Message to send (will be JSON encoded)
        """
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)

    def get_connected_users(self) -> Set[str]:
        """
        Get set of connected user IDs.

        Returns:
            Set of user IDs
        """
        return set(self.active_connections.keys())

    def is_user_connected(self, user_id: str) -> bool:
        """
        Check if user has any active connections.

        Args:
            user_id: User ID

        Returns:
            True if user is connected
        """
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


# Global connection manager instance
connection_manager = ConnectionManager()
