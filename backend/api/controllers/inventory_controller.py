"""
Controller for inventory-related operations.
"""
from fastapi import HTTPException, status
from typing import List

from api.dependencies import inventory_service
from api.serializers import InventoryItemCreate, InventoryItemUpdate
from models import InventoryItem


class InventoryController:
    """Controller for handling inventory operations."""
    
    @staticmethod
    async def get_all_items() -> List[InventoryItem]:
        """Get all inventory items."""
        return await inventory_service.get_all_items()
    
    @staticmethod
    async def get_item_by_id(item_id: str) -> InventoryItem:
        """
        Get a specific inventory item by ID.
        
        Raises:
            HTTPException: If item not found
        """
        item = await inventory_service.get_item_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        return item
    
    @staticmethod
    async def create_item(item: InventoryItemCreate) -> InventoryItem:
        """Create a new inventory item."""
        return await inventory_service.create_item(**item.dict())
    
    @staticmethod
    async def update_item(item_id: str, update: InventoryItemUpdate) -> InventoryItem:
        """
        Update an inventory item.
        
        Raises:
            HTTPException: If item not found
        """
        item = await inventory_service.update_item(
            item_id, 
            **update.dict(exclude_unset=True)
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        return item
    
    @staticmethod
    async def delete_item(item_id: str) -> dict:
        """
        Delete an inventory item.
        
        Raises:
            HTTPException: If item not found
        """
        success = await inventory_service.delete_item(item_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        return {"message": "Item deleted successfully"}
    
    @staticmethod
    async def get_low_stock_items() -> List[InventoryItem]:
        """Get all items with low stock (below threshold)."""
        return await inventory_service.get_low_stock_items()

