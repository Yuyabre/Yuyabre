"""
FastAPI Application - JSON Version (No MongoDB Required)

This is a simplified version that uses JSON storage instead of MongoDB.
Perfect for development and testing!
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger

from utils.json_storage import json_storage
from modules.splitwise import SplitwiseService
from config import settings


# Request/Response Models
class CommandRequest(BaseModel):
    """Request model for agent commands."""
    command: str
    user_id: Optional[str] = None


class CommandResponse(BaseModel):
    """Response model for agent commands."""
    success: bool
    message: str


# Lifespan event handler for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.
    """
    # Startup
    logger.info("Starting Grocery Management Agent API (JSON Version)")
    logger.info(f"Using JSON storage: {json_storage.file_path}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Grocery Management Agent API")


# Create FastAPI app
app = FastAPI(
    title="Grocery Management Agent API (JSON)",
    description="REST API for shared flat grocery management - JSON storage version",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
splitwise_service = SplitwiseService()


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    Check API health.
    """
    return {
        "status": "healthy",
        "storage": "json",
        "storage_path": str(json_storage.file_path),
        "version": "0.1.0",
    }


# Splitwise OAuth endpoints
@app.get("/api/auth/splitwise/authorize", tags=["Splitwise OAuth"])
async def splitwise_authorize(user_id: str):
    """
    Initiate OAuth authorization flow for Splitwise.
    
    This endpoint generates an authorization URL that the user should visit
    to authorize the application to access their Splitwise account.
    
    Args:
        user_id: Internal user ID
        
    Returns:
        JSON with authorization URL
    """
    if not splitwise_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Splitwise not configured"
        )
    
    # Get user from JSON storage
    user = json_storage.find_one(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )
    
    authorize_url = await splitwise_service.get_authorize_url_json(user_id, user)
    
    if not authorize_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )
    
    return {
        "authorize_url": authorize_url
    }


@app.get("/api/auth/splitwise/callback", tags=["Splitwise OAuth"])
async def splitwise_callback(
    oauth_token: str,
    oauth_verifier: str,
    user_id: Optional[str] = None
):
    """
    Handle OAuth callback from Splitwise.
    
    This endpoint receives the OAuth callback after the user authorizes
    the application. It exchanges the request token for an access token
    and stores it for the user.
    
    Args:
        oauth_token: OAuth token from callback
        oauth_verifier: OAuth verifier from callback
        user_id: Internal user ID (optional, can be retrieved from token)
        
    Returns:
        Success message
    """
    if not splitwise_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Splitwise not configured"
        )
    
    # If user_id not provided, try to find user by oauth_token
    if not user_id:
        user = json_storage.find_one(splitwise_oauth_token=oauth_token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not identify user. Please provide user_id or ensure OAuth flow was initiated."
            )
        user_id = user['user_id']
    
    success = await splitwise_service.handle_oauth_callback_json(
        user_id=user_id,
        oauth_token=oauth_token,
        oauth_verifier=oauth_verifier
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete authorization"
        )
    
    return {
        "success": True,
        "message": "Successfully authorized Splitwise. You can now use Splitwise features."
    }


@app.get("/api/auth/splitwise/status/{user_id}", tags=["Splitwise OAuth"])
async def splitwise_auth_status(user_id: str):
    """
    Check if a user has authorized Splitwise.
    
    Args:
        user_id: Internal user ID
        
    Returns:
        Authorization status
    """
    user = json_storage.find_one(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )
    
    is_authorized = bool(
        user.get('splitwise_access_token') and
        user.get('splitwise_access_token_secret')
    )
    
    return {
        "user_id": user_id,
        "authorized": is_authorized,
        "splitwise_user_id": user.get('splitwise_user_id')
    }


# Splitwise endpoints
@app.get("/splitwise/expenses", tags=["Splitwise"])
async def get_splitwise_expenses(user_id: str, limit: int = 20):
    """
    Get recent Splitwise expenses for a user.
    
    Args:
        user_id: Internal user ID (must be authorized)
        limit: Maximum number of expenses to retrieve
    """
    if not splitwise_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Splitwise not configured"
        )
    
    user = json_storage.find_one(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )
    
    is_authorized = bool(
        user.get('splitwise_access_token') and
        user.get('splitwise_access_token_secret')
    )
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized with Splitwise. Please complete OAuth flow first."
        )
    
    # Get expenses using JSON storage
    expenses = await splitwise_service.get_group_expenses_json(user, limit=limit)
    return {"expenses": expenses}


if __name__ == "__main__":
    import uvicorn
    
    logger.add(
        "logs/api_{time}.log",
        rotation="1 day",
        retention="7 days",
        level=settings.log_level,
    )
    
    uvicorn.run(
        "main_json:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
    )

