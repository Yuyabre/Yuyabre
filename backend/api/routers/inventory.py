"""
Router for inventory-related endpoints.
"""

from fastapi import APIRouter, Query, Path
from typing import List, Optional

from api.controllers.inventory_controller import InventoryController
from api.serializers import InventoryItemCreate, InventoryItemUpdate
from models import InventoryItem

router = APIRouter(prefix="/inventory", tags=["Inventory"])

controller = InventoryController()


@router.post("/{user_id}", response_model=InventoryItem)
async def create_inventory_item(
    item: InventoryItemCreate,
    user_id: str = Path(..., description="User ID creating the item"),
) -> InventoryItem:
    """
    Create a new inventory item for a user.

    For personal items (shared=False):
    - Item will be associated with the provided user_id

    For shared items (shared=True):
    - Item will be associated with the user's household
    - User must be in a household
    """
    return await controller.create_item(item, user_id=user_id)


@router.patch("/{item_id}", response_model=InventoryItem)
async def update_inventory_item(
    item_id: str,
    update: InventoryItemUpdate,
    user_id: str = Query(
        ..., description="User ID updating the item (must have access)"
    ),
):
    """
    Update an inventory item.

    User must have access to the item:
    - Personal items: user must own the item
    - Shared items: user must be in the same household
    """
    return await controller.update_item(item_id, update, user_id=user_id)


@router.delete("/{item_id}")
async def delete_inventory_item(
    item_id: str,
    user_id: str = Query(
        ..., description="User ID deleting the item (must have access)"
    ),
):
    """
    Delete an inventory item.

    User must have access to the item:
    - Personal items: user must own the item
    - Shared items: user must be in the same household
    """
    return await controller.delete_item(item_id, user_id=user_id)


@router.get("/low-stock", response_model=List[InventoryItem])
async def get_low_stock(
    user_id: str = Query(..., description="Filter low-stock items for a specific user")
):
    """
    Get all items with low stock (below threshold), optionally filtered by user.

    If user_id is provided, returns low-stock items for that user:
    - Personal items (shared=False) owned by the user
    - Shared items (shared=True) from the user's household

    If user_id is not provided, returns all low-stock items (backward compatibility).
    """
    return await controller.get_low_stock_items(user_id=user_id)


@router.get("/{user_id}", response_model=List[InventoryItem])
async def get_inventory_by_user(user_id: str):
    """
    Get all inventory items for a specific user.

    Returns:
    - Personal items (shared=False) owned by the user
    - ALL shared items (shared=True) from the user's household
      This includes items shared by ALL household members, not just the requesting user.

    This endpoint provides a complete view of all items available to the user,
    including both their personal inventory and all shared household inventory
    (regardless of which household member created the shared items).
    """
    return await controller.get_items_by_user(user_id)
