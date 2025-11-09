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

    def _get_user_client(
        self,
        access_token: str,
        access_token_secret: str
    ) -> Optional[Splitwise]:
        """
        Create a Splitwise client for a specific user using their OAuth tokens.
        
        Args:
            access_token: User's OAuth access token
            access_token_secret: User's OAuth access token secret
            
        Returns:
            Splitwise client instance or None if not configured
        """
        if not settings.splitwise_consumer_key or not settings.splitwise_consumer_secret:
            logger.error("Splitwise credentials not configured")
            return None
        
        try:
            # For OAuth 1.0, the Splitwise library uses api_key for the access token
            # The access_token_secret is stored but not passed to Splitwise constructor
            # OAuth 1.0 signing is handled internally by the library
            client = Splitwise(
                settings.splitwise_consumer_key,
                settings.splitwise_consumer_secret,
                api_key=access_token
            )
            return client
        except Exception as e:
            logger.error(f"Failed to create user Splitwise client: {e}")
            logger.debug(f"Error details: {str(e)}")
            return None
    
    async def get_user_expenses(
        self,
        user_id: str,
        access_token: str,
        access_token_secret: str,
        group_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get recent expenses for a user using their OAuth tokens.
        
        Args:
            user_id: Internal user ID
            access_token: User's OAuth access token
            access_token_secret: User's OAuth access token secret
            group_id: Splitwise group ID (uses default from settings if not provided)
            limit: Maximum number of expenses to retrieve
            
        Returns:
            List of expense dictionaries
        """
        client = self._get_user_client(access_token, access_token_secret)
        if not client:
            logger.error(f"Failed to create client for user {user_id}")
            return []
        
        try:
            # Get expenses - if group_id is provided, filter by group, otherwise get all
            if group_id:
                expenses = client.getExpenses(
                    group_id=int(group_id),
                    limit=limit
                )
            else:
                # Get all expenses (across all groups)
                expenses = client.getExpenses(limit=limit)
            
            return [
                {
                    "id": str(exp.getId()),
                    "description": exp.getDescription(),
                    "cost": str(exp.getCost()),
                    "currency_code": exp.getCurrencyCode() if hasattr(exp, 'getCurrencyCode') else "EUR",
                    "date": exp.getDate().isoformat() if exp.getDate() else None,
                    "category": exp.getCategory().getName() if exp.getCategory() else None,
                    "users": [
                        {
                            "id": str(u.getId()),
                            "owed_share": str(u.getOwedShare()),
                            "paid_share": str(u.getPaidShare()),
                        }
                        for u in exp.getUsers()
                    ] if exp.getUsers() else [],
                }
                for exp in expenses
            ]
            
        except Exception as e:
            logger.error(f"Failed to get user expenses for {user_id}: {e}")
            return []
    
    async def search_groups(
        self,
        user_id: str,
        access_token: str,
        access_token_secret: str,
        query: str
    ) -> List[Dict]:
        """
        Search for Splitwise groups by name.
        
        Args:
            user_id: Internal user ID
            access_token: User's OAuth access token
            access_token_secret: User's OAuth access token secret
            query: Search query (group name)
            
        Returns:
            List of matching group dictionaries
        """
        from requests_oauthlib import OAuth1Session
        from config import settings
        
        try:
            # Create OAuth session
            oauth = OAuth1Session(
                settings.splitwise_consumer_key,
                client_secret=settings.splitwise_consumer_secret,
                resource_owner_key=access_token,
                resource_owner_secret=access_token_secret
            )
            
            # Get all groups
            response = oauth.get("https://secure.splitwise.com/api/v3.0/get_groups")
            response.raise_for_status()
            data = response.json()
            
            groups = data.get("groups", [])
            
            # Filter groups by name (case-insensitive partial match)
            query_lower = query.lower()
            matching_groups = [
                {
                    "id": str(group.get("id", "")),
                    "name": group.get("name", ""),
                    "created_at": group.get("created_at"),
                    "updated_at": group.get("updated_at"),
                    "members": [
                        {
                            "id": str(member.get("id", "")),
                            "first_name": member.get("first_name", ""),
                            "last_name": member.get("last_name", ""),
                            "email": member.get("email", ""),
                        }
                        for member in group.get("members", [])
                    ],
                }
                for group in groups
                if query_lower in group.get("name", "").lower()
            ]
            
            logger.info(f"Found {len(matching_groups)} matching groups for query '{query}'")
            return matching_groups
            
        except Exception as e:
            logger.error(f"Failed to search groups for user {user_id}: {e}")
            return []
    
    async def create_user_expense(
        self,
        user_id: str,
        access_token: str,
        access_token_secret: str,
        description: str,
        amount: float,
        splitwise_user_ids: List[str],
        group_id: Optional[str] = None,
        category: str = "Groceries",
        date: Optional[datetime] = None,
        notes: Optional[str] = None,
        split_method: str = "equal",
        paid_by_user_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a new expense in Splitwise using user's OAuth tokens.
        
        Args:
            user_id: Internal user ID
            access_token: User's OAuth access token
            access_token_secret: User's OAuth access token secret
            description: Description of the expense
            amount: Total amount to split
            splitwise_user_ids: List of Splitwise user IDs to split among
            group_id: Splitwise group ID (optional)
            category: Expense category (default: "Groceries")
            date: Date of the expense (default: now)
            notes: Additional notes
            split_method: How to split the expense ("equal" by default)
            paid_by_user_id: Splitwise user ID of the person who paid (defaults to first user)
            
        Returns:
            Expense ID if successful, None otherwise
        """
        from config import settings
        
        try:
            # Validate that we have at least 2 users for splitting
            if len(splitwise_user_ids) < 2:
                logger.warning(
                    f"Cannot create Splitwise expense with only {len(splitwise_user_ids)} user(s). "
                    f"Splitwise requires at least 2 users to split an expense."
                )
                return None
            
            # Prepare expense data
            expense_date = date or datetime.utcnow()
            
            # Calculate split amounts
            if split_method == "equal":
                split_amount = amount / len(splitwise_user_ids) if splitwise_user_ids else amount
            else:
                # For now, only support equal split
                split_amount = amount / len(splitwise_user_ids) if splitwise_user_ids else amount
            
            # Determine who paid (default to current user/creator if not specified)
            # Ensure paid_by is a string for comparison
            paid_by = str(paid_by_user_id) if paid_by_user_id else (str(splitwise_user_ids[0]) if splitwise_user_ids else None)
            
            # Use Splitwise SDK correctly (as per user's example)
            # Create Splitwise client
            logger.debug(f"Creating Splitwise client with consumer key: {settings.splitwise_consumer_key[:10]}...")
            s_obj = Splitwise(
                settings.splitwise_consumer_key,
                settings.splitwise_consumer_secret
            )
            # Set access token using setAccessToken method
            # The library expects a dictionary with oauth_token and oauth_token_secret
            logger.debug(f"Setting access token (token preview: {access_token[:10] if access_token else 'None'}...)")
            token_dict = {
                'oauth_token': access_token,
                'oauth_token_secret': access_token_secret
            }
            s_obj.setAccessToken(token_dict)
            logger.debug("✓ Access token set successfully")
            
            # Create expense object
            expense = Expense()
            expense.setCost(f"{amount:.2f}")
            expense.setDescription(description)
            # Set date as string in ISO format
            expense.setDate(expense_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            
            if group_id:
                expense.setGroupId(int(group_id))
            
            if notes:
                expense.setDetails(notes)
            
            # IMPORTANT: All group members are included by default (as per user requirement)
            # Build users array using ExpenseUser objects
            expense_users = []
            for sw_user_id in splitwise_user_ids:
                # Ensure sw_user_id is a string for comparison
                sw_user_id_str = str(sw_user_id)
                expense_user = ExpenseUser()
                expense_user.setId(int(sw_user_id_str))
                
                if sw_user_id_str == paid_by:
                    # Person who paid: they paid the full amount, but only owe their share
                    expense_user.setPaidShare(f"{amount:.2f}")
                    expense_user.setOwedShare(f"{split_amount:.2f}")
                else:
                    # Others: didn't pay anything, owe their share
                    expense_user.setPaidShare("0.00")
                    expense_user.setOwedShare(f"{split_amount:.2f}")
                
                expense_users.append(expense_user)
            
            # Set users using setUsers method (not addUser)
            expense.setUsers(expense_users)
            
            # Verify the math
            total_paid = sum(float(u.getPaidShare()) for u in expense_users)
            total_owed = sum(float(u.getOwedShare()) for u in expense_users)
            logger.debug(f"Expense validation: cost={amount}, total_paid={total_paid:.2f}, total_owed={total_owed:.2f}, users_count={len(expense_users)}")
            
            # Create expense using SDK
            logger.debug(f"Creating Splitwise expense: {description} (€{amount:.2f}) with {len(expense_users)} users")
            created_expense, errors = s_obj.createExpense(expense)
            
            if errors:
                error_messages = []
                # Handle errors - could be a list, string, or other type
                if isinstance(errors, (list, tuple)):
                    for error in errors:
                        if hasattr(error, 'getMessage'):
                            error_messages.append(error.getMessage())
                        else:
                            error_messages.append(str(error))
                elif isinstance(errors, str):
                    error_messages.append(errors)
                else:
                    error_messages.append(str(errors))
                
                error_text = "; ".join(error_messages) if error_messages else str(errors)
                logger.error(f"Splitwise SDK returned errors: {error_text}")
                logger.debug(f"Full error response: {errors} (type: {type(errors)})")
                return None
            
            if created_expense:
                expense_id = str(created_expense.getId())
                logger.info(
                    f"Created Splitwise expense: {description} "
                    f"(€{amount:.2f}) - ID: {expense_id}"
                )
                return expense_id
            else:
                logger.error("Splitwise SDK returned no expense")
                return None
                
        except Exception as e:
            import traceback
            logger.error(f"Failed to create Splitwise expense: {type(e).__name__}: {e}")
            logger.debug(f"Error details: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def get_current_user_id(
        self,
        user_id: str,
        access_token: str,
        access_token_secret: str,
    ) -> Optional[str]:
        """
        Get the current user's Splitwise user ID from the API.
        
        Args:
            user_id: Internal user ID
            access_token: User's OAuth access token
            access_token_secret: User's OAuth access token secret
            
        Returns:
            Splitwise user ID if successful, None otherwise
        """
        from requests_oauthlib import OAuth1Session
        from config import settings
        
        try:
            # Create OAuth session
            oauth = OAuth1Session(
                settings.splitwise_consumer_key,
                client_secret=settings.splitwise_consumer_secret,
                resource_owner_key=access_token,
                resource_owner_secret=access_token_secret
            )
            
            # Get current user info
            response = oauth.get("https://secure.splitwise.com/api/v3.0/get_current_user")
            response.raise_for_status()
            user_data = response.json()
            
            if "user" in user_data and "id" in user_data["user"]:
                splitwise_user_id = str(user_data["user"]["id"])
                logger.info(f"Retrieved Splitwise user ID {splitwise_user_id} for user {user_id}")
                return splitwise_user_id
            else:
                logger.warning("Splitwise API response missing user ID")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get current user ID for {user_id}: {e}")
            return None
    
    async def get_group_members(
        self,
        user_id: str,
        access_token: str,
        access_token_secret: str,
        group_id: str,
    ) -> List[Dict]:
        """
        Get all members of a Splitwise group.
        
        Args:
            user_id: Internal user ID
            access_token: User's OAuth access token
            access_token_secret: User's OAuth access token secret
            group_id: Splitwise group ID
            
        Returns:
            List of group member dictionaries with id, first_name, last_name, email
        """
        from requests_oauthlib import OAuth1Session
        from config import settings
        
        try:
            # Create OAuth session
            oauth = OAuth1Session(
                settings.splitwise_consumer_key,
                client_secret=settings.splitwise_consumer_secret,
                resource_owner_key=access_token,
                resource_owner_secret=access_token_secret
            )
            
            # Get group details
            response = oauth.get(f"https://secure.splitwise.com/api/v3.0/get_group/{group_id}")
            response.raise_for_status()
            data = response.json()
            
            group = data.get("group", {})
            members = group.get("members", [])
            
            member_list = [
                {
                    "id": str(member.get("id", "")),
                    "first_name": member.get("first_name", ""),
                    "last_name": member.get("last_name", ""),
                    "email": member.get("email", ""),
                }
                for member in members
            ]
            
            logger.info(f"Retrieved {len(member_list)} members from Splitwise group {group_id}")
            return member_list
            
        except Exception as e:
            logger.error(f"Failed to get group members for group {group_id}: {e}")
            return []

