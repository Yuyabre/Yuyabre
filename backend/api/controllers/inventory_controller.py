"""
Controller for inventory-related operations.
"""

from fastapi import HTTPException, status
from typing import List, Optional

from api.dependencies import inventory_service
from api.serializers import InventoryItemCreate, InventoryItemUpdate
from models import InventoryItem
from models.user import User


class InventoryController:
    """Controller for handling inventory operations."""

    @staticmethod
    async def _verify_user_access_to_item(item: InventoryItem, user_id: str) -> bool:
        """
        Verify that a user has access to an inventory item.

        User has access if:
        - Item is personal (shared=False) and user_id matches item.user_id
        - Item is shared (shared=True) and user's household_id matches item.household_id

        Args:
            item: The inventory item to check
            user_id: The user's ID

        Returns:
            True if user has access, False otherwise
        """
        if not item:
            return False

        # Personal item - must be owned by user
        if not item.shared and item.user_id == user_id:
            return True

        # Shared item - must be in user's household
        if item.shared and item.household_id:
            user = await User.find_one(User.user_id == user_id)
            if user and user.household_id == item.household_id:
                return True

        return False

    @staticmethod
    async def get_all_items(user_id: Optional[str] = None) -> List[InventoryItem]:
        """
        Get all inventory items, optionally filtered by user.

        Args:
            user_id: Optional user ID to filter items for a specific user

        Returns:
            List of InventoryItems
        """
        if user_id:
            # Verify user exists
            user = await User.find_one(User.user_id == user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found: {user_id}",
                )
            return await inventory_service.get_all_items(user_id=user_id)
        else:
            # Backward compatibility: return all items (consider deprecating)
            return await inventory_service.get_all_items()

    @staticmethod
    async def create_item(item: InventoryItemCreate, user_id: str) -> InventoryItem:
        """
        Create a new inventory item for a user.

        Args:
            item: Item creation data
            user_id: The user creating the item

        Returns:
            Created InventoryItem

        Raises:
            HTTPException: If user not found or validation fails
        """
        # Verify user exists
        user = await User.find_one(User.user_id == user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        # Prepare item data
        item_data = item.dict()

        # If shared=False, user_id is required
        if not item.shared:
            if not item_data.get("user_id"):
                item_data["user_id"] = user_id

        # If shared=True, use user's household_id
        if item.shared:
            if not user.household_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User must be in a household to create shared items",
                )
            item_data["household_id"] = user.household_id
            # Don't set user_id for shared items
            item_data.pop("user_id", None)

        return await inventory_service.create_item(**item_data)

    @staticmethod
    async def update_item(
        item_id: str, update: InventoryItemUpdate, user_id: str
    ) -> InventoryItem:
        """
        Update an inventory item.

        Args:
            item_id: The item's unique identifier
            update: Update data
            user_id: The user updating the item (must have access)

        Returns:
            Updated InventoryItem

        Raises:
            HTTPException: If item not found or user doesn't have access
        """
        # Get item first to verify access
        item = await inventory_service.get_item_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )

        # Verify user has access
        has_access = await InventoryController._verify_user_access_to_item(
            item, user_id
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to update this item",
            )

        # Update the item
        updated_item = await inventory_service.update_item(
            item_id, **update.dict(exclude_unset=True)
        )
        if not updated_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )
        return updated_item

    @staticmethod
    async def delete_item(item_id: str, user_id: str) -> dict:
        """
        Delete an inventory item.

        Args:
            item_id: The item's unique identifier
            user_id: The user deleting the item (must have access)

        Returns:
            Success message

        Raises:
            HTTPException: If item not found or user doesn't have access
        """
        # Get item first to verify access
        item = await inventory_service.get_item_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )

        # Verify user has access
        has_access = await InventoryController._verify_user_access_to_item(
            item, user_id
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to delete this item",
            )

        success = await inventory_service.delete_item(item_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )
        return {"message": "Item deleted successfully"}

    @staticmethod
    async def get_low_stock_items(user_id: Optional[str] = None) -> List[InventoryItem]:
        """
        Get all items with low stock (below threshold), optionally filtered by user.

        Args:
            user_id: Optional user ID to filter items for a specific user

        Returns:
            List of low-stock InventoryItems
        """
        if user_id:
            # Verify user exists
            user = await User.find_one(User.user_id == user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found: {user_id}",
                )
            return await inventory_service.get_low_stock_items(user_id=user_id)
        else:
            # Backward compatibility: return all low-stock items (consider deprecating)
            return await inventory_service.get_low_stock_items()

    @staticmethod
    async def get_items_by_user(user_id: str) -> List[InventoryItem]:
        """
        Get all inventory items for a specific user.

        Returns:
        - Personal items (shared=False) owned by the user
        - ALL shared items (shared=True) from the user's household
          This includes items shared by ALL household members, not just the requesting user.

        Args:
            user_id: The user's unique identifier

        Returns:
            List of InventoryItems for the user (personal + all shared household items)

        Raises:
            HTTPException: If user not found
        """
        from models.user import User

        # Verify user exists
        user = await User.find_one(User.user_id == user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        return await inventory_service.get_all_items(user_id=user_id)
