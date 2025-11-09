"""
User Inventory Model - MongoDB schema for tracking individual user inventory for shared items.
"""
from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import Field
from uuid import uuid4


class UserInventory(Document):
    """
    Tracks individual user's portion of shared inventory items.
    
    This is used when items are shared among housemates to track
    how much each person has consumed or is responsible for.
    
    Attributes:
        user_inventory_id: Unique identifier
        user_id: User who owns this inventory entry
        item_id: Reference to the shared inventory item
        item_name: Name of the item (denormalized for quick access)
        quantity: How much this user has/needs
        unit: Unit of measurement
        last_updated: When this was last updated
    """
    
    user_inventory_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., min_length=1)
    item_id: str = Field(..., min_length=1)
    item_name: str = Field(..., min_length=1, max_length=200)
    quantity: float = Field(ge=0)
    unit: str = Field(..., min_length=1, max_length=50)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_inventory"
        indexes = [
            "user_inventory_id",
            "user_id",
            "item_id",
            ("user_id", "item_id"),  # Compound index for lookups
        ]
    
    def update_quantity(self, delta: float) -> None:
        """
        Update the quantity by a delta amount.
        
        Args:
            delta: Amount to add (positive) or remove (negative)
        """
        self.quantity = max(0, self.quantity + delta)
        self.last_updated = datetime.utcnow()
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_inventory_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user123",
                "item_id": "item456",
                "item_name": "Milk",
                "quantity": 1.5,
                "unit": "liters",
                "last_updated": "2025-11-08T10:00:00Z",
            }
        }

