"""
Router for inventory-related endpoints.
"""
from fastapi import APIRouter
from typing import List

from api.controllers.inventory_controller import InventoryController
from api.serializers import InventoryItemCreate, InventoryItemUpdate
from models import InventoryItem

router = APIRouter(prefix="/inventory", tags=["Inventory"])

controller = InventoryController()


@router.get("", response_model=List[InventoryItem])
async def get_inventory():
    """Get all inventory items."""
    return await controller.get_all_items()


@router.get("/{item_id}", response_model=InventoryItem)
async def get_inventory_item(item_id: str):
    """Get a specific inventory item by ID."""
    return await controller.get_item_by_id(item_id)


@router.post("", response_model=InventoryItem)
async def create_inventory_item(item: InventoryItemCreate):
    """Create a new inventory item."""
    return await controller.create_item(item)


@router.patch("/{item_id}", response_model=InventoryItem)
async def update_inventory_item(item_id: str, update: InventoryItemUpdate):
    """Update an inventory item."""
    return await controller.update_item(item_id, update)


@router.delete("/{item_id}")
async def delete_inventory_item(item_id: str):
    """Delete an inventory item."""
    return await controller.delete_item(item_id)


@router.get("/low-stock", response_model=List[InventoryItem])
async def get_low_stock():
    """Get all items with low stock (below threshold)."""
    return await controller.get_low_stock_items()

