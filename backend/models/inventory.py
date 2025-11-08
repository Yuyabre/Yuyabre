"""
Inventory Item Model - MongoDB schema for grocery inventory tracking.
"""
from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import Field
from uuid import uuid4


class InventoryItem(Document):
    """
    Represents a single item in the grocery inventory.
    
    Attributes:
        item_id: Unique identifier for the inventory item
        name: Name of the grocery item (e.g., "Milk", "Eggs")
        category: Category of the item (e.g., "Dairy", "Vegetables")
        quantity: Current quantity in inventory
        unit: Unit of measurement (e.g., "liters", "pieces", "kg")
        threshold: Minimum quantity before triggering low-stock alert
        last_updated: Timestamp of last inventory update
        expiration_date: Optional expiration date for perishable items
        shared: Whether this item is shared among all flatmates
        brand: Preferred brand (optional)
        price: Last known price
        notes: Additional notes about the item
    """
    
    item_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    quantity: float = Field(ge=0)
    unit: str = Field(..., min_length=1, max_length=50)
    threshold: float = Field(default=1.0, ge=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    expiration_date: Optional[datetime] = None
    shared: bool = Field(default=True)
    brand: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None
    
    class Settings:
        name = "inventory"
        indexes = [
            "item_id",
            "name",
            "category",
        ]
    
    def is_low_stock(self) -> bool:
        """Check if item is below threshold."""
        return self.quantity <= self.threshold
    
    def is_expired(self) -> bool:
        """Check if item has expired."""
        if self.expiration_date is None:
            return False
        return datetime.utcnow() > self.expiration_date
    
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
                "item_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Milk",
                "category": "Dairy",
                "quantity": 2.0,
                "unit": "liters",
                "threshold": 1.0,
                "last_updated": "2025-11-08T10:00:00Z",
                "expiration_date": "2025-11-15T00:00:00Z",
                "shared": True,
                "brand": "Melkunie",
                "price": 1.79,
                "notes": "Semi-skimmed"
            }
        }

