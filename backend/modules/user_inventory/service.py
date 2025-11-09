"""
User Inventory Service - Manages individual user inventory for shared items.
"""
from typing import List, Optional
from datetime import datetime
from loguru import logger

from models.user_inventory import UserInventory
from models.inventory import InventoryItem


class UserInventoryService:
    """
    Service for managing individual user inventory for shared items.
    """
    
    async def get_user_inventory(
        self,
        user_id: str,
        item_id: Optional[str] = None
    ) -> List[UserInventory]:
        """
        Get user's inventory items.
        
        Args:
            user_id: User ID
            item_id: Optional item ID to filter by
            
        Returns:
            List of UserInventory items
        """
        if item_id:
            items = await UserInventory.find(
                UserInventory.user_id == user_id,
                UserInventory.item_id == item_id
            ).to_list()
        else:
            items = await UserInventory.find(
                UserInventory.user_id == user_id
            ).to_list()
        
        return items
    
    async def update_user_inventory(
        self,
        user_id: str,
        item_id: str,
        item_name: str,
        quantity_delta: float,
        unit: str,
    ) -> UserInventory:
        """
        Update user's inventory for a shared item.
        
        Args:
            user_id: User ID
            item_id: Inventory item ID
            item_name: Item name
            quantity_delta: Change in quantity (positive to add, negative to remove)
            unit: Unit of measurement
            
        Returns:
            Updated UserInventory
        """
        # Find or create user inventory entry
        user_inventory = await UserInventory.find_one(
            UserInventory.user_id == user_id,
            UserInventory.item_id == item_id
        )
        
        if not user_inventory:
            # Create new entry
            user_inventory = UserInventory(
                user_id=user_id,
                item_id=item_id,
                item_name=item_name,
                quantity=max(0, quantity_delta),
                unit=unit,
            )
            await user_inventory.insert()
            logger.info(f"Created user inventory entry for {user_id}: {item_name}")
        else:
            # Update existing entry
            user_inventory.update_quantity(quantity_delta)
            await user_inventory.save()
            logger.info(f"Updated user inventory for {user_id}: {item_name} ({quantity_delta:+})")
        
        return user_inventory
    
    async def update_from_order(
        self,
        order_item,
        user_ids: List[str],
    ) -> None:
        """
        Update user inventories from an order item.
        
        Distributes the order quantity among the users who requested it.
        
        Args:
            order_item: OrderItem from the order
            user_ids: List of user IDs who requested this item
        """
        if not user_ids:
            return
        
        # Get the shared inventory item
        inventory_item = await InventoryItem.find_one(
            InventoryItem.name == order_item.name
        )
        
        if not inventory_item or not inventory_item.shared:
            # Not a shared item, skip
            return
        
        # Distribute quantity equally among users (or proportionally)
        quantity_per_user = order_item.quantity / len(user_ids)
        
        for user_id in user_ids:
            await self.update_user_inventory(
                user_id=user_id,
                item_id=inventory_item.item_id,
                item_name=order_item.name,
                quantity_delta=quantity_per_user,
                unit=order_item.unit,
            )
        
        logger.info(
            f"Updated user inventories for {order_item.name}: "
            f"{order_item.quantity} {order_item.unit} distributed among {len(user_ids)} users"
        )

