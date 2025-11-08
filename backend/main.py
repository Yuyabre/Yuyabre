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
from models import InventoryItem, Order
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


# Splitwise endpoints
@app.get("/splitwise/expenses", tags=["Splitwise"])
async def get_splitwise_expenses(limit: int = 20):
    """
    Get recent Splitwise expenses.
    """
    if not splitwise_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Splitwise not configured"
        )
    
    expenses = await splitwise_service.get_group_expenses(limit=limit)
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

