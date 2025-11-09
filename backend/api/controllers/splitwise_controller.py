"""
Controller for Splitwise-related operations.
"""
from fastapi import HTTPException, status

from modules.splitwise.service import SplitwiseService
from modules.splitwise.oauth import SplitwiseOAuthService
from models.user import User


class SplitwiseController:
    """Controller for handling Splitwise operations."""
    
    def __init__(self):
        self.splitwise_service = SplitwiseService()
        self.oauth_service = SplitwiseOAuthService()
    
    async def get_expenses(self, user_id: str, limit: int = 20) -> dict:
        """
        Get recent Splitwise expenses for a user.
        
        Args:
            user_id: Internal user ID
            limit: Maximum number of expenses to retrieve
        
        Raises:
            HTTPException: If user not authorized or Splitwise not configured
        """
        # Check if user is authorized
        if not await self.oauth_service.is_user_authorized(user_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authorized with Splitwise. Please connect your Splitwise account."
            )
        
        # Get user to retrieve OAuth tokens
        user = await User.find_one(User.user_id == user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get expenses using user's OAuth tokens
        expenses = await self.splitwise_service.get_user_expenses(
            user_id=user_id,
            access_token=user.splitwise_access_token,
            access_token_secret=user.splitwise_access_token_secret,
            limit=limit
        )
        
        return {"expenses": expenses}

