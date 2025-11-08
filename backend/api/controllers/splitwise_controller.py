"""
Controller for Splitwise-related operations.
"""
from fastapi import HTTPException, status

from api.dependencies import splitwise_service


class SplitwiseController:
    """Controller for handling Splitwise operations."""
    
    @staticmethod
    async def get_expenses(limit: int = 20) -> dict:
        """
        Get recent Splitwise expenses.
        
        Raises:
            HTTPException: If Splitwise is not configured
        """
        if not splitwise_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Splitwise not configured"
            )
        
        expenses = await splitwise_service.get_group_expenses(limit=limit)
        return {"expenses": expenses}

