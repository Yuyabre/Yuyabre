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
    
    async def search_groups(self, user_id: str, query: str) -> dict:
        """
        Search for Splitwise groups by name.
        
        Args:
            user_id: Internal user ID
            query: Group name to search for
        
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
        
        # Search groups using user's OAuth tokens
        groups = await self.splitwise_service.search_groups(
            user_id=user_id,
            access_token=user.splitwise_access_token,
            access_token_secret=user.splitwise_access_token_secret,
            query=query
        )
        
        return {"groups": groups}
    
    async def create_expense(
        self,
        user_id: str,
        description: str,
        amount: float,
        splitwise_user_ids: list,
        group_id: str = None,
        category: str = "Groceries",
        date: str = None,
        notes: str = None,
        split_method: str = "equal",
        paid_by_user_id: str = None,
    ) -> dict:
        """
        Create a new expense in Splitwise.
        
        Args:
            user_id: Internal user ID
            description: Description of the expense
            amount: Total amount to split
            splitwise_user_ids: List of Splitwise user IDs to split among
            group_id: Splitwise group ID (optional)
            category: Expense category (default: "Groceries")
            date: ISO format date string (optional)
            notes: Additional notes (optional)
            split_method: How to split the expense (default: "equal")
            paid_by_user_id: Splitwise user ID of person who paid (optional)
        
        Raises:
            HTTPException: If user not authorized or Splitwise not configured
        """
        from datetime import datetime
        
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
        
        # Parse date if provided
        expense_date = None
        if date:
            try:
                expense_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use ISO format (e.g., '2025-01-01T00:00:00Z')"
                )
        
        # Create expense using user's OAuth tokens
        expense_id = await self.splitwise_service.create_user_expense(
            user_id=user_id,
            access_token=user.splitwise_access_token,
            access_token_secret=user.splitwise_access_token_secret,
            description=description,
            amount=amount,
            splitwise_user_ids=splitwise_user_ids,
            group_id=group_id,
            category=category,
            date=expense_date,
            notes=notes,
            split_method=split_method,
            paid_by_user_id=paid_by_user_id,
        )
        
        if not expense_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create expense in Splitwise. Check server logs for details."
            )
        
        return {
            "success": True,
            "expense_id": expense_id,
            "message": f"Expense '{description}' created successfully"
        }

