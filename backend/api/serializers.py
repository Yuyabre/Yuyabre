"""
Request and Response serializers (Pydantic models) for the API.
"""
from pydantic import BaseModel
from typing import List, Optional


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


class MessageResponse(BaseModel):
    """Generic message response model."""
    message: str

