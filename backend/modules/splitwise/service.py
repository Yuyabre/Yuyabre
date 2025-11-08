"""
Splitwise Service - Integration with Splitwise API for expense management.
"""
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger
from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.user import ExpenseUser

from config import settings


class SplitwiseService:
    """
    Service class for managing Splitwise expenses.
    
    Provides methods to create, update, and retrieve expenses from Splitwise.
    """
    
    def __init__(self):
        """Initialize Splitwise client."""
        if not settings.splitwise_consumer_key or not settings.splitwise_consumer_secret:
            logger.warning("Splitwise credentials not configured")
            self.client = None
        else:
            self.client = Splitwise(
                settings.splitwise_consumer_key,
                settings.splitwise_consumer_secret,
                api_key=settings.splitwise_api_key
            )
            logger.info("Splitwise client initialized")
    
    def is_configured(self) -> bool:
        """Check if Splitwise is properly configured."""
        return self.client is not None
    
    async def create_expense(
        self,
        description: str,
        amount: float,
        user_ids: List[str],
        group_id: Optional[str] = None,
        category: str = "Groceries",
        date: Optional[datetime] = None,
        notes: Optional[str] = None,
        split_method: str = "equal",
    ) -> Optional[str]:
        """
        Create a new expense in Splitwise.
        
        Args:
            description: Description of the expense
            amount: Total amount to split
            user_ids: List of Splitwise user IDs to split among
            group_id: Splitwise group ID (uses default from settings if not provided)
            category: Expense category (default: "Groceries")
            date: Date of the expense (default: now)
            notes: Additional notes
            split_method: How to split the expense ("equal" by default)
            
        Returns:
            Expense ID if successful, None otherwise
        """
        if not self.is_configured():
            logger.error("Splitwise not configured")
            return None
        
        try:
            expense = Expense()
            expense.setCost(str(amount))
            expense.setDescription(description)
            expense.setDate(date or datetime.utcnow())
            expense.setGroupId(group_id or settings.splitwise_group_id)
            expense.setCategory(category)
            
            if notes:
                expense.setDetails(notes)
            
            # Set up equal split among all users
            split_amount = amount / len(user_ids)
            
            users = []
            for user_id in user_ids:
                user = ExpenseUser()
                user.setId(int(user_id))
                user.setOwedShare(str(split_amount))
                user.setPaidShare("0")
                users.append(user)
            
            # First user pays the full amount
            if users:
                users[0].setPaidShare(str(amount))
            
            expense.setUsers(users)
            
            # Create the expense
            created_expense = self.client.createExpense(expense)
            expense_id = str(created_expense.getId())
            
            logger.info(
                f"Created Splitwise expense: {description} "
                f"(€{amount:.2f}) - ID: {expense_id}"
            )
            return expense_id
            
        except Exception as e:
            logger.error(f"Failed to create Splitwise expense: {e}")
            return None
    
    async def get_expense(self, expense_id: str) -> Optional[Dict]:
        """
        Retrieve an expense by ID.
        
        Args:
            expense_id: Splitwise expense ID
            
        Returns:
            Expense details as dictionary, None if not found
        """
        if not self.is_configured():
            logger.error("Splitwise not configured")
            return None
        
        try:
            expense = self.client.getExpense(int(expense_id))
            
            return {
                "id": str(expense.getId()),
                "description": expense.getDescription(),
                "cost": float(expense.getCost()),
                "date": expense.getDate(),
                "category": expense.getCategory().getName() if expense.getCategory() else None,
                "created_at": expense.getCreatedAt(),
                "updated_at": expense.getUpdatedAt(),
            }
            
        except Exception as e:
            logger.error(f"Failed to get Splitwise expense {expense_id}: {e}")
            return None
    
    async def update_expense(
        self,
        expense_id: str,
        description: Optional[str] = None,
        amount: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Update an existing expense.
        
        Args:
            expense_id: Splitwise expense ID
            description: New description
            amount: New amount
            notes: New notes
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            logger.error("Splitwise not configured")
            return False
        
        try:
            expense = self.client.getExpense(int(expense_id))
            
            if description:
                expense.setDescription(description)
            if amount:
                expense.setCost(str(amount))
            if notes:
                expense.setDetails(notes)
            
            self.client.updateExpense(expense)
            logger.info(f"Updated Splitwise expense: {expense_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Splitwise expense {expense_id}: {e}")
            return False
    
    async def delete_expense(self, expense_id: str) -> bool:
        """
        Delete an expense.
        
        Args:
            expense_id: Splitwise expense ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            logger.error("Splitwise not configured")
            return False
        
        try:
            expense = self.client.getExpense(int(expense_id))
            self.client.deleteExpense(expense)
            logger.info(f"Deleted Splitwise expense: {expense_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete Splitwise expense {expense_id}: {e}")
            return False
    
    async def get_group_expenses(
        self,
        group_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get recent expenses for a group.
        
        Args:
            group_id: Splitwise group ID (uses default from settings if not provided)
            limit: Maximum number of expenses to retrieve
            
        Returns:
            List of expense dictionaries
        """
        if not self.is_configured():
            logger.error("Splitwise not configured")
            return []
        
        try:
            expenses = self.client.getExpenses(
                group_id=int(group_id or settings.splitwise_group_id),
                limit=limit
            )
            
            return [
                {
                    "id": str(exp.getId()),
                    "description": exp.getDescription(),
                    "cost": float(exp.getCost()),
                    "date": exp.getDate(),
                    "category": exp.getCategory().getName() if exp.getCategory() else None,
                }
                for exp in expenses
            ]
            
        except Exception as e:
            logger.error(f"Failed to get group expenses: {e}")
            return []

