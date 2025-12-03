"""
Connection service for managing WebSocket connections
"""
import logging
from typing import Set

from chatService import get_socketio

logger = logging.getLogger(__name__)


class ConnectionService:
    """Service for managing client connections"""
    
    def __init__(self):
        self._active_connections: Set[str] = set()
    
    def add_connection(self, sid: str):
        """
        Add a new connection
        
        Args:
            sid: Socket session ID
        """
        self._active_connections.add(sid)
        logger.info(f"Client connected: {sid} (Total: {len(self._active_connections)})")
    
    def remove_connection(self, sid: str):
        """
        Remove a connection
        
        Args:
            sid: Socket session ID
        """
        self._active_connections.discard(sid)
        logger.info(f"Client disconnected: {sid} (Total: {len(self._active_connections)})")
    
    def get_connection_count(self) -> int:
        """
        Get total number of active connections
        
        Returns:
            Number of active connections
        """
        return len(self._active_connections)
    
    def is_connected(self, sid: str) -> bool:
        """
        Check if a connection is active
        
        Args:
            sid: Socket session ID
            
        Returns:
            True if connected, False otherwise
        """
        return sid in self._active_connections


# Global connection service instance
connection_service = ConnectionService()

