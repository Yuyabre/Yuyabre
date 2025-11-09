"""
FastAPI Application - REST API for the Grocery Management Agent.

Provides HTTP endpoints for web/mobile interfaces to interact with the agent.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger

from database import db
from agent.core import GroceryAgent
from modules.inventory import InventoryService
from modules.ordering import OrderingService
from modules.splitwise import SplitwiseService
from models import InventoryItem, Order, User
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


class InventoryItemCreate(BaseModel):
    """Request model for creating inventory items."""
    name: str
    category: str
    quantity: float
    unit: str
    threshold: float = 1.0
    shared: bool = True
    brand: Optional[str] = None
    price: Optional[float] = None


class InventoryItemUpdate(BaseModel):
    """Request model for updating inventory items."""
    quantity: Optional[float] = None
    threshold: Optional[float] = None
    notes: Optional[str] = None


# Lifespan event handler for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.
    
    Handles database connection on startup and cleanup on shutdown.
    """
    # Startup
    logger.info("Starting Grocery Management Agent API")
    await db.connect()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Grocery Management Agent API")
    await db.close()


# Create FastAPI app
app = FastAPI(
    title="Grocery Management Agent API",
    description="REST API for shared flat grocery management and automation",
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
agent = GroceryAgent()
inventory_service = InventoryService()
ordering_service = OrderingService()
splitwise_service = SplitwiseService()


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    Check API and database health.
    """
    db_status = await db.ping()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "version": "0.1.0",
    }


# Agent endpoints
@app.post("/agent/command", response_model=CommandResponse, tags=["Agent"])
async def process_command(request: CommandRequest):
    """
    Process a natural language command through the agent.
    
    The agent will parse the intent and execute the appropriate action.
    """
    try:
        response = await agent.process_command(request.command, request.user_id)
        return CommandResponse(success=True, message=response)
    except Exception as e:
        logger.error(f"Error processing command: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Inventory endpoints
@app.get("/inventory", response_model=List[InventoryItem], tags=["Inventory"])
async def get_inventory():
    """
    Get all inventory items.
    """
    return await inventory_service.get_all_items()


@app.get("/inventory/{item_id}", response_model=InventoryItem, tags=["Inventory"])
async def get_inventory_item(item_id: str):
    """
    Get a specific inventory item by ID.
    """
    item = await inventory_service.get_item_by_id(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item


@app.post("/inventory", response_model=InventoryItem, tags=["Inventory"])
async def create_inventory_item(item: InventoryItemCreate):
    """
    Create a new inventory item.
    """
    return await inventory_service.create_item(**item.dict())


@app.patch("/inventory/{item_id}", response_model=InventoryItem, tags=["Inventory"])
async def update_inventory_item(item_id: str, update: InventoryItemUpdate):
    """
    Update an inventory item.
    """
    item = await inventory_service.update_item(item_id, **update.dict(exclude_unset=True))
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item


@app.delete("/inventory/{item_id}", tags=["Inventory"])
async def delete_inventory_item(item_id: str):
    """
    Delete an inventory item.
    """
    success = await inventory_service.delete_item(item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return {"message": "Item deleted successfully"}


@app.get("/inventory/low-stock", response_model=List[InventoryItem], tags=["Inventory"])
async def get_low_stock():
    """
    Get all items with low stock (below threshold).
    """
    return await inventory_service.get_low_stock_items()


# Order endpoints
@app.get("/orders", response_model=List[Order], tags=["Orders"])
async def get_orders(limit: int = 20):
    """
    Get recent order history.
    """
    return await ordering_service.get_order_history(limit)


@app.get("/orders/{order_id}", response_model=Order, tags=["Orders"])
async def get_order(order_id: str):
    """
    Get a specific order by ID.
    """
    order = await Order.find_one(Order.order_id == order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


@app.post("/orders/{order_id}/cancel", tags=["Orders"])
async def cancel_order(order_id: str):
    """
    Cancel an order.
    """
    success = await ordering_service.cancel_order(order_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel order"
        )
    return {"message": "Order cancelled successfully"}


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
    
    authorize_url = await splitwise_service.get_authorize_url(user_id)
    
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
        user = await User.find_one(User.splitwise_oauth_token == oauth_token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not identify user. Please provide user_id or ensure OAuth flow was initiated."
            )
        user_id = user.user_id
    
    success = await splitwise_service.handle_oauth_callback(
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
    is_authorized = await splitwise_service.is_user_authorized(user_id)
    
    return {
        "user_id": user_id,
        "authorized": is_authorized
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
    
    if not await splitwise_service.is_user_authorized(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized with Splitwise. Please complete OAuth flow first."
        )
    
    # Get user and convert to dict format for JSON-compatible method
    user = await User.find_one(User.user_id == user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )
    
    # Convert User object to dict format
    user_data = {
        'splitwise_access_token': user.splitwise_access_token,
        'splitwise_access_token_secret': user.splitwise_access_token_secret,
    }
    
    expenses = await splitwise_service.get_group_expenses_json(user_data, limit=limit)
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
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
    )

