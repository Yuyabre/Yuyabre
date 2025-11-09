"""
WebSocket Connection Manager - Manages WebSocket connections with timeout and cleanup.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


class WebSocketConnection:
    """Represents a single WebSocket connection with metadata."""
    
    def __init__(self, websocket: WebSocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.is_active = True
        self.timeout_task: Optional[asyncio.Task] = None
    
    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def is_expired(self, timeout_minutes: int = 5) -> bool:
        """Check if connection has expired based on timeout."""
        if not self.is_active:
            return True
        timeout = timedelta(minutes=timeout_minutes)
        return datetime.utcnow() - self.last_activity > timeout


class WebSocketManager:
    """
    Manages WebSocket connections with automatic timeout and cleanup.
    """
    
    def __init__(self, timeout_minutes: int = 5):
        """
        Initialize WebSocket manager.
        
        Args:
            timeout_minutes: Minutes of inactivity before auto-closing connection (default: 5)
        """
        self.connections: Dict[str, WebSocketConnection] = {}
        self.timeout_minutes = timeout_minutes
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def _start_cleanup_task(self):
        """Start the periodic cleanup task (lazy initialization)."""
        try:
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        except RuntimeError:
            # No event loop running yet, will start later
            pass
    
    async def _periodic_cleanup(self):
        """Periodically clean up expired connections."""
        try:
            while True:
                await asyncio.sleep(60)  # Run every minute
                await self.cleanup_expired_connections()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")
    
    def generate_connection_id(self, websocket: WebSocket) -> str:
        """Generate a unique connection ID."""
        # Use client info to create a unique ID
        client = websocket.client
        if client:
            return f"{client.host}:{client.port}-{id(websocket)}"
        return f"unknown-{id(websocket)}"
    
    async def accept_connection(self, websocket: WebSocket) -> str:
        """
        Accept a new WebSocket connection and register it.
        
        Args:
            websocket: The WebSocket connection to accept
            
        Returns:
            Connection ID
        """
        await websocket.accept()
        
        # Start cleanup task if not already running (lazy initialization)
        self._start_cleanup_task()
        
        connection_id = self.generate_connection_id(websocket)
        
        connection = WebSocketConnection(websocket, connection_id)
        self.connections[connection_id] = connection
        
        # Start timeout task for this connection
        connection.timeout_task = asyncio.create_task(
            self._connection_timeout_handler(connection_id)
        )
        
        logger.info(f"WebSocket connection accepted: {connection_id}")
        return connection_id
    
    async def _connection_timeout_handler(self, connection_id: str):
        """
        Handle connection timeout - close connection after inactivity period.
        
        Checks every 30 seconds if the connection has expired.
        
        Args:
            connection_id: ID of the connection to monitor
        """
        try:
            check_interval = 30  # Check every 30 seconds
            timeout_seconds = self.timeout_minutes * 60
            
            while True:
                await asyncio.sleep(check_interval)
                
                # Check if connection still exists and is expired
                if connection_id not in self.connections:
                    break
                
                connection = self.connections[connection_id]
                if not connection.is_active:
                    break
                
                # Check if expired
                time_since_activity = (datetime.utcnow() - connection.last_activity).total_seconds()
                if time_since_activity >= timeout_seconds:
                    logger.info(f"Closing WebSocket connection due to timeout: {connection_id}")
                    await self.close_connection(connection_id, reason="timeout")
                    break
        except asyncio.CancelledError:
            # Task was cancelled (connection closed normally)
            pass
        except Exception as e:
            logger.error(f"Error in timeout handler for {connection_id}: {e}")
    
    async def close_connection(self, connection_id: str, reason: str = "normal"):
        """
        Close a WebSocket connection and clean up.
        
        Args:
            connection_id: ID of the connection to close
            reason: Reason for closing (for logging)
        """
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        connection.is_active = False
        
        # Cancel timeout task
        if connection.timeout_task and not connection.timeout_task.done():
            connection.timeout_task.cancel()
        
        # Close WebSocket
        try:
            await connection.websocket.close()
        except Exception as e:
            logger.debug(f"Error closing WebSocket {connection_id}: {e}")
        
        # Remove from connections
        del self.connections[connection_id]
        logger.info(f"WebSocket connection closed: {connection_id} (reason: {reason})")
    
    def update_activity(self, connection_id: str):
        """
        Update the last activity timestamp for a connection.
        This resets the timeout timer.
        
        Args:
            connection_id: ID of the connection
        """
        if connection_id in self.connections:
            self.connections[connection_id].update_activity()
    
    async def send_message(self, connection_id: str, message: dict) -> bool:
        """
        Send a message to a WebSocket connection.
        
        Args:
            connection_id: ID of the connection
            message: Message to send (will be JSON encoded)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        if not connection.is_active:
            return False
        
        try:
            await connection.websocket.send_json(message)
            connection.update_activity()
            return True
        except WebSocketDisconnect:
            logger.info(f"Client disconnected while sending message: {connection_id}")
            await self.close_connection(connection_id, reason="client_disconnect")
            return False
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            await self.close_connection(connection_id, reason="send_error")
            return False
    
    async def receive_message(self, connection_id: str) -> Optional[str]:
        """
        Receive a message from a WebSocket connection.
        
        Args:
            connection_id: ID of the connection
            
        Returns:
            Received message text, or None if connection closed
        """
        if connection_id not in self.connections:
            return None
        
        connection = self.connections[connection_id]
        if not connection.is_active:
            return None
        
        try:
            data = await connection.websocket.receive_text()
            connection.update_activity()
            return data
        except WebSocketDisconnect:
            logger.info(f"Client disconnected while receiving: {connection_id}")
            await self.close_connection(connection_id, reason="client_disconnect")
            return None
        except Exception as e:
            logger.error(f"Error receiving message from {connection_id}: {e}")
            await self.close_connection(connection_id, reason="receive_error")
            return None
    
    async def cleanup_expired_connections(self):
        """
        Clean up expired connections (called periodically).
        """
        expired_connections = [
            conn_id for conn_id, conn in self.connections.items()
            if conn.is_expired(self.timeout_minutes)
        ]
        
        for conn_id in expired_connections:
            await self.close_connection(conn_id, reason="expired")
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len([c for c in self.connections.values() if c.is_active])
    
    async def close_all_connections(self):
        """Close all active connections (for shutdown)."""
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        connection_ids = list(self.connections.keys())
        for conn_id in connection_ids:
            await self.close_connection(conn_id, reason="shutdown")


# Global WebSocket manager instance
websocket_manager = WebSocketManager(timeout_minutes=5)

