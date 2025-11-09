"""
Controller for system-related operations (health checks, etc.).
"""
from database import db


class SystemController:
    """Controller for handling system operations."""
    
    @staticmethod
    async def health_check() -> dict:
        """
        Check API and database health.
        
        Returns:
            Dictionary with health status information
        """
        db_status = await db.ping()
        
        return {
            "status": "healthy" if db_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "version": "0.1.0",
        }

