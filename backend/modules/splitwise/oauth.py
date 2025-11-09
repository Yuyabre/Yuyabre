"""
Splitwise OAuth Service - Handles OAuth 1.0 authentication flow.
"""
import traceback
from typing import Optional, Tuple, Dict
from loguru import logger
from requests_oauthlib import OAuth1Session
from splitwise import Splitwise

from config import settings
from models.user import User


class SplitwiseOAuthService:
    """
    Service for handling Splitwise OAuth 1.0 authentication flow.
    
    Provides methods to:
    - Get authorization URL for user
    - Exchange tokens after user authorization
    - Check if user is authorized
    """
    
    # Temporary storage for request tokens (in production, use Redis or database)
    _request_tokens: Dict[str, Tuple[str, str]] = {}
    
    def __init__(self):
        """Initialize OAuth service with consumer credentials."""
        if not settings.splitwise_consumer_key or not settings.splitwise_consumer_secret:
            logger.warning("Splitwise OAuth credentials not configured")
            self.consumer_key = None
            self.consumer_secret = None
        else:
            self.consumer_key = settings.splitwise_consumer_key
            self.consumer_secret = settings.splitwise_consumer_secret
            logger.info("Splitwise OAuth service initialized")
            logger.debug(f"Consumer Key: {self.consumer_key[:10]}... (first 10 chars)")
            logger.info("Note: Callback URL is managed by frontend/Splitwise app settings")
    
    def is_configured(self) -> bool:
        """Check if OAuth service is properly configured."""
        configured = self.consumer_key is not None and self.consumer_secret is not None
        if not configured:
            logger.warning("Splitwise OAuth not configured - missing consumer_key or consumer_secret")
        else:
            logger.debug(f"Splitwise OAuth configured - Consumer Key: {self.consumer_key[:10]}...")
        return configured
    
    async def get_authorization_url(self, user_id: str) -> Optional[str]:
        """
        Get the authorization URL for a user to connect their Splitwise account.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            Authorization URL if successful, None otherwise
        """
        if not self.is_configured():
            logger.error("Splitwise OAuth not configured - missing consumer key or secret")
            return None
        
        logger.info(f"Starting OAuth flow for user {user_id}")
        logger.debug("Callback URL will be determined by Splitwise app settings")
        
        try:
            # Verify user exists
            user = await User.find_one(User.user_id == user_id)
            if not user:
                logger.error(f"User {user_id} not found in database")
                return None
            
            logger.debug(f"User {user_id} found: {user.name}")
            
            # Create OAuth1 session (callback URL is set in Splitwise app settings)
            logger.debug("Creating OAuth1Session with consumer credentials")
            logger.debug("Note: Callback URL is managed by Splitwise app settings, not sent in request")
            oauth = OAuth1Session(
                self.consumer_key,
                client_secret=self.consumer_secret
            )
            
            # Request token
            request_token_url = "https://secure.splitwise.com/api/v3.0/get_request_token"
            logger.debug(f"Requesting token from: {request_token_url}")
            
            try:
                fetch_response = oauth.fetch_request_token(request_token_url)
                logger.debug(f"Token request response: {list(fetch_response.keys())}")
            except Exception as token_error:
                error_type = type(token_error).__name__
                logger.error(f"Token request failed: {error_type}: {token_error}")
                logger.error(f"Consumer Key (first 10): {self.consumer_key[:10] if self.consumer_key else 'None'}...")
                logger.error(f"Consumer Secret (first 10): {self.consumer_secret[:10] if self.consumer_secret else 'None'}...")
                logger.error(f"Request token URL: {request_token_url}")
                logger.error("Note: Callback URL is managed by Splitwise app settings")
                
                # Try to get more details from the error
                if hasattr(token_error, 'response'):
                    response = token_error.response
                    logger.error(f"Response status: {getattr(response, 'status_code', 'N/A')}")
                    logger.error(f"Response headers: {dict(getattr(response, 'headers', {}))}")
                    try:
                        response_text = getattr(response, 'text', 'N/A')
                        logger.error(f"Response text (first 500 chars): {response_text[:500]}")
                    except:
                        logger.error("Could not read response text")
                    
                    # Check for common issues
                    if hasattr(response, 'status_code'):
                        if response.status_code == 401:
                            logger.error("=" * 80)
                            logger.error("401 Unauthorized - 'Invalid OAuth Request'")
                            logger.error("=" * 80)
                            logger.error("Common causes:")
                            logger.error("  1. Consumer Key and Secret are incorrect or swapped")
                            logger.error("  2. Callback URL in Splitwise app settings doesn't match frontend")
                            logger.error("     Check: https://secure.splitwise.com/apps")
                            logger.error("  3. Callback URL must end with '/callback', not '/authorize'")
                            logger.error("  4. If using ngrok, URL changes on restart - update Splitwise settings")
                            logger.error("  5. App not properly registered or credentials invalid")
                            logger.error("=" * 80)
                            logger.error("VERIFICATION STEPS:")
                            logger.error(f"  1. Go to: https://secure.splitwise.com/apps")
                            logger.error(f"  2. Find your app and check the 'Redirect URI' field")
                            logger.error(f"  3. It MUST match the callback URL configured in your frontend")
                            logger.error(f"  4. Current Consumer Key starts with: {self.consumer_key[:10]}...")
                            logger.error(f"  5. Current Consumer Secret starts with: {self.consumer_secret[:10]}...")
                            logger.error("=" * 80)
                        elif response.status_code == 400:
                            logger.error("400 Bad Request - OAuth request format may be incorrect")
                
                # Log the full exception for debugging
                logger.error(f"Full traceback:\n{traceback.format_exc()}")
                raise
            
            # Store request token and secret for later use
            request_token = fetch_response.get('oauth_token')
            request_token_secret = fetch_response.get('oauth_token_secret')
            
            logger.debug(f"Request token received: {request_token[:10] if request_token else 'None'}...")
            
            if not request_token or not request_token_secret:
                logger.error("Failed to get request token - response missing oauth_token or oauth_token_secret")
                logger.error(f"Response keys: {list(fetch_response.keys())}")
                logger.error(f"Response values: {fetch_response}")
                return None
            
            # Store tokens temporarily (keyed by request token, not user_id, since we'll get user_id in callback)
            self._request_tokens[request_token] = (user_id, request_token_secret)
            logger.debug(f"Stored request token for user {user_id}. Total stored tokens: {len(self._request_tokens)}")
            
            # Get authorization URL
            base_authorization_url = "https://secure.splitwise.com/oauth/authorize"
            authorization_url = oauth.authorization_url(base_authorization_url)
            
            logger.info(f"Successfully generated authorization URL for user {user_id}")
            logger.debug(f"Authorization URL: {authorization_url[:100]}...")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Failed to get authorization URL for user {user_id}: {type(e).__name__}: {e}")
            logger.exception("Full traceback:")
            return None
    
    async def handle_callback(
        self,
        oauth_token: str,
        oauth_verifier: str
    ) -> Tuple[Optional[str], bool]:
        """
        Handle OAuth callback and exchange tokens for access tokens.
        
        Args:
            oauth_token: OAuth token from callback (request token)
            oauth_verifier: OAuth verifier from callback
            
        Returns:
            Tuple of (user_id, success) if successful, (None, False) otherwise
        """
        if not self.is_configured():
            logger.error("Splitwise OAuth not configured")
            return None, False
        
        logger.info(f"Handling OAuth callback with token: {oauth_token[:10] if oauth_token else 'None'}...")
        logger.debug(f"OAuth verifier: {oauth_verifier[:10] if oauth_verifier else 'None'}...")
        
        try:
            # Retrieve stored request token secret
            if oauth_token not in self._request_tokens:
                logger.error(f"Request token {oauth_token} not found in stored tokens")
                logger.debug(f"Available tokens: {list(self._request_tokens.keys())[:5]}...")
                return None, False
            
            user_id, request_token_secret = self._request_tokens.pop(oauth_token)
            logger.debug(f"Retrieved request token secret for user {user_id}")
            
            # Create OAuth1 session with request token
            logger.debug("Creating OAuth1Session with request token for access token exchange")
            oauth = OAuth1Session(
                self.consumer_key,
                client_secret=self.consumer_secret,
                resource_owner_key=oauth_token,
                resource_owner_secret=request_token_secret,
                verifier=oauth_verifier
            )
            
            # Exchange for access token
            access_token_url = "https://secure.splitwise.com/api/v3.0/get_access_token"
            logger.debug(f"Exchanging for access token at: {access_token_url}")
            
            try:
                oauth_tokens = oauth.fetch_access_token(access_token_url)
                logger.debug(f"Access token response keys: {list(oauth_tokens.keys())}")
            except Exception as token_error:
                logger.error(f"Access token exchange failed: {type(token_error).__name__}: {token_error}")
                if hasattr(token_error, 'response'):
                    logger.error(f"Response status: {token_error.response.status_code if hasattr(token_error.response, 'status_code') else 'N/A'}")
                    logger.error(f"Response text: {getattr(token_error.response, 'text', 'N/A')[:500]}")
                raise
            
            access_token = oauth_tokens.get('oauth_token')
            access_token_secret = oauth_tokens.get('oauth_token_secret')
            
            if not access_token or not access_token_secret:
                logger.error("Failed to get access token - response missing tokens")
                logger.error(f"Response: {oauth_tokens}")
                return None, False
            
            logger.debug(f"Access token received: {access_token[:10]}...")
            
            # Update user with access tokens
            user = await User.find_one(User.user_id == user_id)
            if not user:
                logger.error(f"User {user_id} not found during callback")
                return None, False
            
            user.splitwise_access_token = access_token
            user.splitwise_access_token_secret = access_token_secret
            logger.debug(f"Updated user {user_id} with access tokens")
            
            # Get user's Splitwise user ID using authenticated client
            try:
                logger.debug("Fetching Splitwise user info to get user ID")
                client = Splitwise(
                    self.consumer_key,
                    self.consumer_secret,
                    api_key=access_token,
                    api_secret=access_token_secret
                )
                current_user = client.getCurrentUser()
                splitwise_user_id = str(current_user.getId())
                user.splitwise_user_id = splitwise_user_id
                logger.debug(f"Retrieved Splitwise user ID: {splitwise_user_id}")
            except Exception as e:
                logger.warning(f"Could not get Splitwise user ID: {type(e).__name__}: {e}")
                logger.debug("Continuing without Splitwise user ID")
            
            await user.save()
            logger.info(f"Successfully authorized Splitwise for user {user_id} (name: {user.name})")
            
            return user_id, True
            
        except Exception as e:
            logger.error(f"Failed to handle OAuth callback: {type(e).__name__}: {e}")
            logger.exception("Full traceback:")
            return None, False
    
    async def is_user_authorized(self, user_id: str) -> bool:
        """
        Check if a user has authorized Splitwise.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            True if user has valid access tokens, False otherwise
        """
        try:
            user = await User.find_one(User.user_id == user_id)
            if not user:
                return False
            
            return (
                user.splitwise_access_token is not None and
                user.splitwise_access_token_secret is not None
            )
        except Exception as e:
            logger.error(f"Error checking authorization status: {e}")
            return False

