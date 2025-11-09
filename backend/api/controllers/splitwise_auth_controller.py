"""
Controller for Splitwise OAuth authentication operations.
"""
from fastapi import HTTPException, status, Query
from loguru import logger

from modules.splitwise.oauth import SplitwiseOAuthService
from config import settings


class SplitwiseAuthController:
    """Controller for handling Splitwise OAuth authentication."""
    
    def __init__(self):
        self.oauth_service = SplitwiseOAuthService()
    
    async def get_authorization_url(self, user_id: str, callback_url: str) -> dict:
        """
        Get the authorization URL for connecting Splitwise.
        
        Args:
            user_id: Internal user ID
            callback_url: Callback URL where Splitwise will redirect after authorization
            
        Returns:
            Dictionary with authorize_url
        """
        logger.info(f"Authorization request received for user_id: {user_id}, callback_url: {callback_url}")
        
        if not self.oauth_service.is_configured():
            logger.error("Splitwise OAuth service not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Splitwise not configured"
            )
        
        authorize_url = await self.oauth_service.get_authorization_url(user_id, callback_url)
        
        if not authorize_url:
            logger.error(f"Failed to generate authorization URL for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate authorization URL. Check server logs for details."
            )
        
        logger.info(f"Successfully generated authorization URL for user {user_id}")
        return {"authorize_url": authorize_url}
    
    async def handle_callback(
        self,
        oauth_token: str = Query(..., alias="oauth_token"),
        oauth_verifier: str = Query(..., alias="oauth_verifier")
    ) -> dict:
        """
        Handle OAuth callback from Splitwise.
        
        Args:
            oauth_token: OAuth token from callback
            oauth_verifier: OAuth verifier from callback
            
        Returns:
            Success message
        """
        if not self.oauth_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Splitwise not configured"
            )
        
        user_id, success = await self.oauth_service.handle_callback(
            oauth_token,
            oauth_verifier
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to authorize Splitwise. Please try again."
            )
        
        return {
            "success": True,
            "message": "Successfully authorized Splitwise. You can now use Splitwise features."
        }
    
    async def handle_callback_post(
        self,
        user_id: str,
        oauth_token: str,
        oauth_verifier: str
    ) -> dict:
        """
        Handle OAuth callback from frontend.
        
        This endpoint receives OAuth token and verifier from the frontend
        and exchanges them for access tokens, storing them in the database.
        
        Args:
            user_id: Internal user ID
            oauth_token: OAuth token from callback
            oauth_verifier: OAuth verifier from callback
            
        Returns:
            Success message
        """
        if not self.oauth_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Splitwise not configured"
            )
        
        logger.info(f"Handling OAuth callback POST for user {user_id}")
        
        # Verify the user_id matches the stored token
        # The oauth_service will handle the token exchange and storage
        result_user_id, success = await self.oauth_service.handle_callback(
            oauth_token,
            oauth_verifier
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to authorize Splitwise. Please try again."
            )
        
        # Verify the user_id matches
        if result_user_id != user_id:
            logger.warning(
                f"User ID mismatch: expected {user_id}, got {result_user_id}. "
                "This might indicate a token reuse or timing issue."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID mismatch. Please try the authorization flow again."
            )
        
        return {
            "success": True,
            "message": "Successfully authorized Splitwise. You can now use Splitwise features."
        }
    
    async def get_authorization_status(self, user_id: str) -> dict:
        """
        Check if user has authorized Splitwise.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            Dictionary with authorization status
        """
        if not self.oauth_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Splitwise not configured"
            )
        
        authorized = await self.oauth_service.is_user_authorized(user_id)
        
        return {
            "user_id": user_id,
            "authorized": authorized
        }

