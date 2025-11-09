"""
Splitwise Service - Integration with Splitwise API for expense management.
Supports OAuth 1.0 authentication flow.

All operations use direct API calls with requests-oauthlib (no SDK dependency).
- OAuth flow: Manual implementation using requests-oauthlib
- Expense creation: Direct API calls (see agent/core.py)
- Expense retrieval: Direct API calls to get_expenses endpoint
"""
from typing import List, Optional, Dict
from loguru import logger

from config import settings
from models.user import User


class SplitwiseService:
    """
    Service class for managing Splitwise expenses with OAuth support.
    
    Provides methods to:
    - Initiate OAuth authorization flow
    - Handle OAuth callbacks and exchange tokens
    - Create, update, and retrieve expenses using user-specific tokens
    """
    
    def __init__(self):
        """Initialize Splitwise service with consumer credentials."""
        if not settings.splitwise_consumer_key or not settings.splitwise_consumer_secret:
            logger.warning("Splitwise credentials not configured")
            self.consumer_key = None
            self.consumer_secret = None
        else:
            self.consumer_key = settings.splitwise_consumer_key
            self.consumer_secret = settings.splitwise_consumer_secret
            logger.info("Splitwise service initialized with OAuth credentials")
    
    def is_configured(self) -> bool:
        """Check if Splitwise is properly configured."""
        return self.consumer_key is not None and self.consumer_secret is not None
    
    async def get_authorize_url(self, user_id: str) -> Optional[str]:
        """
        Get the OAuth authorization URL for a user.
        
        This initiates the OAuth flow by getting a request token and
        generating the authorization URL that the user should visit.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            Authorization URL to redirect user to, or None if error
        """
        if not self.is_configured():
            logger.error("Splitwise not configured")
            return None
        
        try:
            # Get user from database
            user = await User.find_one(User.user_id == user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return None
            
            # Use manual OAuth flow (SDK doesn't properly support OAuth 1.0)
            return await self._get_authorize_url_manual(user)
                
        except Exception as e:
            logger.error(f"Failed to get authorization URL: {e}", exc_info=True)
            return None
    
    async def _get_authorize_url_manual(self, user: User) -> Optional[str]:
        """
        Manual OAuth 1.0 flow implementation.
        
        This is a fallback if the SDK doesn't provide the method directly.
        """
        try:
            import requests
            from requests_oauthlib import OAuth1
            
            # Step 1: Get request token
            request_token_url = "https://secure.splitwise.com/oauth/request_token"
            oauth = OAuth1(
                self.consumer_key,
                client_secret=self.consumer_secret,
                callback_uri=settings.splitwise_callback_url
            )
            
            response = requests.post(request_token_url, auth=oauth)
            
            if response.status_code != 200:
                logger.error(f"Failed to get request token: {response.status_code} - {response.text}")
                return None
            
            # Parse response (format: oauth_token=xxx&oauth_token_secret=yyy)
            from urllib.parse import parse_qs
            credentials = parse_qs(response.text)
            oauth_token = credentials.get('oauth_token', [None])[0]
            oauth_token_secret = credentials.get('oauth_token_secret', [None])[0]
            
            if not oauth_token or not oauth_token_secret:
                logger.error("Failed to parse request token from response")
                return None
            
            # Store temporary tokens in user object
            user.splitwise_oauth_token = oauth_token
            user.splitwise_oauth_token_secret = oauth_token_secret
            await user.save()
            
            # Step 2: Generate authorization URL
            authorize_url = f"https://secure.splitwise.com/oauth/authorize?oauth_token={oauth_token}"
            
            logger.info(f"Generated manual authorization URL for user {user.user_id}")
            return authorize_url
            
        except ImportError:
            logger.error("requests-oauthlib not installed. Install it with: pip install requests-oauthlib")
            return None
        except Exception as e:
            logger.error(f"Failed in manual OAuth flow: {e}", exc_info=True)
            return None
    
    async def handle_oauth_callback(
        self,
        user_id: str,
        oauth_token: str,
        oauth_verifier: str
    ) -> bool:
        """
        Handle OAuth callback and exchange request token for access token.
        
        Args:
            user_id: Internal user ID
            oauth_token: OAuth token from callback (should match stored request token)
            oauth_verifier: OAuth verifier from callback
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            logger.error("Splitwise not configured")
            return False
        
        try:
            # Get user from database
            user = await User.find_one(User.user_id == user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # Verify the token matches what we stored
            if user.splitwise_oauth_token != oauth_token:
                logger.error(f"OAuth token mismatch for user {user_id}")
                return False
            
            # Exchange request token for access token (using manual method)
            access_token, access_token_secret = await self._exchange_tokens_manual(
                oauth_token,
                user.splitwise_oauth_token_secret,
                oauth_verifier
            )
            
            if not access_token or not access_token_secret:
                logger.error(f"Failed to exchange tokens for user {user_id}")
                return False
            
            # Store access tokens in user object
            user.splitwise_access_token = access_token
            user.splitwise_access_token_secret = access_token_secret
            
            # Clear temporary tokens
            user.splitwise_oauth_token = None
            user.splitwise_oauth_token_secret = None
            
            # Get user info from Splitwise to store splitwise_user_id (using direct API call)
            try:
                import requests
                from requests_oauthlib import OAuth1
                
                session = requests.Session()
                session.auth = OAuth1(
                    self.consumer_key,
                    client_secret=self.consumer_secret,
                    resource_owner_key=access_token,
                    resource_owner_secret=access_token_secret
                )
                
                response = session.get('https://secure.splitwise.com/api/v3.0/get_current_user')
                if response.status_code == 200:
                    user_data = response.json()
                    user.splitwise_user_id = str(user_data['user']['id'])
                    logger.info(f"Stored Splitwise user ID: {user.splitwise_user_id}")
            except Exception as e:
                logger.warning(f"Could not fetch current user info: {e}")
            
            await user.save()
            
            logger.info(f"Successfully authorized Splitwise for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle OAuth callback: {e}", exc_info=True)
            return False
    
    async def _exchange_tokens_manual(
        self,
        oauth_token: str,
        oauth_token_secret: str,
        oauth_verifier: str
    ) -> tuple:
        """
        Manually exchange request token for access token.
        
        Returns:
            Tuple of (access_token, access_token_secret) or (None, None) if failed
        """
        try:
            import requests
            from requests_oauthlib import OAuth1
            
            access_token_url = "https://secure.splitwise.com/oauth/access_token"
            
            oauth = OAuth1(
                self.consumer_key,
                client_secret=self.consumer_secret,
                resource_owner_key=oauth_token,
                resource_owner_secret=oauth_token_secret,
                verifier=oauth_verifier
            )
            
            response = requests.post(access_token_url, auth=oauth)
            
            if response.status_code != 200:
                logger.error(f"Failed to exchange tokens: {response.status_code} - {response.text}")
                return None, None
            
            # Parse response
            from urllib.parse import parse_qs
            credentials = parse_qs(response.text)
            access_token = credentials.get('oauth_token', [None])[0]
            access_token_secret = credentials.get('oauth_token_secret', [None])[0]
            
            return access_token, access_token_secret
            
        except ImportError:
            logger.error("requests-oauthlib not installed. Install it with: pip install requests-oauthlib")
            return None, None
        except Exception as e:
            logger.error(f"Failed to exchange tokens: {e}", exc_info=True)
            return None, None
    
    async def is_user_authorized(self, user_id: str) -> bool:
        """
        Check if a user has authorized Splitwise.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            True if user has valid OAuth tokens, False otherwise
        """
        try:
            user = await User.find_one(User.user_id == user_id)
            if not user:
                return False
            
            return bool(
                user.splitwise_access_token and
                user.splitwise_access_token_secret
            )
        except Exception as e:
            logger.error(f"Error checking authorization: {e}")
            return False
    
    # ============================================
    # JSON Storage Compatible Methods
    # ============================================
    
    async def get_authorize_url_json(self, user_id: str, user_data: dict) -> Optional[str]:
        """
        Get authorization URL using JSON storage user data.
        
        Args:
            user_id: Internal user ID
            user_data: User dictionary from JSON storage
            
        Returns:
            Authorization URL or None
        """
        return await self._get_authorize_url_manual_json(user_data)
    
    async def _get_authorize_url_manual_json(self, user_data: dict) -> Optional[str]:
        """Manual OAuth flow for JSON storage."""
        try:
            import requests
            from requests_oauthlib import OAuth1
            from utils.json_storage import json_storage
            from config import settings
            
            # Step 1: Get request token
            request_token_url = "https://secure.splitwise.com/oauth/request_token"
            oauth = OAuth1(
                self.consumer_key,
                client_secret=self.consumer_secret,
                callback_uri=settings.splitwise_callback_url
            )
            
            response = requests.post(request_token_url, auth=oauth)
            
            if response.status_code != 200:
                logger.error(f"Failed to get request token: {response.status_code} - {response.text}")
                return None
            
            # Parse response
            from urllib.parse import parse_qs
            credentials = parse_qs(response.text)
            oauth_token = credentials.get('oauth_token', [None])[0]
            oauth_token_secret = credentials.get('oauth_token_secret', [None])[0]
            
            if not oauth_token or not oauth_token_secret:
                logger.error("Failed to parse request token from response")
                return None
            
            # Store temporary tokens in user data
            json_storage.update(user_data['user_id'], {
                'splitwise_oauth_token': oauth_token,
                'splitwise_oauth_token_secret': oauth_token_secret
            })
            
            # Step 2: Generate authorization URL
            authorize_url = f"https://secure.splitwise.com/oauth/authorize?oauth_token={oauth_token}"
            
            logger.info(f"Generated manual authorization URL for user {user_data['user_id']}")
            return authorize_url
            
        except ImportError:
            logger.error("requests-oauthlib not installed. Install it with: pip install requests-oauthlib")
            return None
        except Exception as e:
            logger.error(f"Failed in manual OAuth flow: {e}", exc_info=True)
            return None
    
    async def handle_oauth_callback_json(
        self,
        user_id: str,
        oauth_token: str,
        oauth_verifier: str
    ) -> bool:
        """
        Handle OAuth callback using JSON storage.
        
        Args:
            user_id: Internal user ID
            oauth_token: OAuth token from callback
            oauth_verifier: OAuth verifier from callback
            
        Returns:
            True if successful, False otherwise
        """
        from utils.json_storage import json_storage
        
        try:
            # Get user from JSON storage
            user = json_storage.find_one(user_id=user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # Verify the token matches what we stored
            if user.get('splitwise_oauth_token') != oauth_token:
                logger.error(f"OAuth token mismatch for user {user_id}")
                return False
            
            # Exchange request token for access token
            access_token, access_token_secret = await self._exchange_tokens_manual(
                oauth_token,
                user.get('splitwise_oauth_token_secret'),
                oauth_verifier
            )
            
            if not access_token or not access_token_secret:
                logger.error(f"Failed to exchange tokens for user {user_id}")
                return False
            
            # Get user info from Splitwise to store splitwise_user_id (using direct API call)
            splitwise_user_id = None
            try:
                import requests
                from requests_oauthlib import OAuth1
                
                session = requests.Session()
                session.auth = OAuth1(
                    self.consumer_key,
                    client_secret=self.consumer_secret,
                    resource_owner_key=access_token,
                    resource_owner_secret=access_token_secret
                )
                
                response = session.get('https://secure.splitwise.com/api/v3.0/get_current_user')
                if response.status_code == 200:
                    user_data = response.json()
                    splitwise_user_id = str(user_data['user']['id'])
                    logger.info(f"Stored Splitwise user ID: {splitwise_user_id}")
            except Exception as e:
                logger.warning(f"Could not fetch current user info: {e}")
            
            # Update user in JSON storage
            json_storage.update(user_id, {
                'splitwise_access_token': access_token,
                'splitwise_access_token_secret': access_token_secret,
                'splitwise_user_id': splitwise_user_id,
                'splitwise_oauth_token': None,
                'splitwise_oauth_token_secret': None
            })
            
            logger.info(f"Successfully authorized Splitwise for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle OAuth callback: {e}", exc_info=True)
            return False
    
    async def get_group_expenses_json(
        self,
        user_data: dict,
        group_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get recent expenses for a group using JSON storage user data.
        
        Args:
            user_data: User dictionary from JSON storage
            group_id: Splitwise group ID (uses default from settings if not provided)
            limit: Maximum number of expenses to retrieve
            
        Returns:
            List of expense dictionaries
        """
        if not self.is_configured():
            logger.error("Splitwise not configured")
            return []
        
        try:
            import requests
            from requests_oauthlib import OAuth1
            from config import settings
            
            if not user_data.get('splitwise_access_token') or not user_data.get('splitwise_access_token_secret'):
                logger.error("User not authorized with Splitwise")
                return []
            
            # Create OAuth session
            session = requests.Session()
            session.auth = OAuth1(
                self.consumer_key,
                client_secret=self.consumer_secret,
                resource_owner_key=user_data['splitwise_access_token'],
                resource_owner_secret=user_data['splitwise_access_token_secret']
            )
            
            # Build API URL
            group_id_to_use = group_id or settings.splitwise_group_id
            if group_id_to_use:
                url = f'https://secure.splitwise.com/api/v3.0/get_expenses?group_id={group_id_to_use}&limit={limit}'
            else:
                url = f'https://secure.splitwise.com/api/v3.0/get_expenses?limit={limit}'
            
            # Make API call
            response = session.get(url)
            
            if response.status_code != 200:
                logger.error(f"Failed to get expenses: {response.status_code} - {response.text}")
                return []
            
            result = response.json()
            
            # Parse expenses from response
            expenses = []
            if 'expenses' in result:
                for exp in result['expenses']:
                    expenses.append({
                        "id": str(exp.get('id', '')),
                        "description": exp.get('description', ''),
                        "cost": float(exp.get('cost', 0)),
                        "date": exp.get('date', ''),
                        "category": exp.get('category', {}).get('name') if exp.get('category') else None,
                    })
            
            return expenses
            
        except Exception as e:
            logger.error(f"Failed to get group expenses: {e}", exc_info=True)
            return []
