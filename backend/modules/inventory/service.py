"""
Inventory Service - Business logic for inventory management.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger

from models.inventory import InventoryItem
from utils.cache import get_inventory_cache, cached_query


class InventoryService:
    """
    Service class for managing grocery inventory.
    
    Provides CRUD operations and business logic for inventory items.
    """

    def __init__(self):
        """Initialize inventory service with cache."""
        self.cache = get_inventory_cache()
        logger.debug("InventoryService initialized with cache")

    def _log_db_query(self, operation: str, **details: Any) -> None:
        """
        Log MongoDB queries executed through the inventory service.
        """
        logger.debug("[MongoDB] inventory_items.{} | {}", operation, details)
    
    async def _invalidate_cache(self) -> None:
        """Invalidate all inventory cache entries."""
        await self.cache.invalidate("inventory")
    
    async def create_item(
        self,
        name: str,
        category: str,
        quantity: float,
        unit: str,
        threshold: float = 1.0,
        expiration_date: Optional[datetime] = None,
        shared: bool = True,
        user_id: Optional[str] = None,
        household_id: Optional[str] = None,
        brand: Optional[str] = None,
        price: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> InventoryItem:
        """
        Create a new inventory item.
        
        Args:
            name: Name of the item
            category: Category (e.g., "Dairy", "Vegetables")
            quantity: Current quantity
            unit: Unit of measurement
            threshold: Low-stock threshold
            expiration_date: Expiration date (for perishable items)
            shared: Whether item is shared among flatmates
            user_id: User ID for personal items (required if shared=False)
            household_id: Household ID for shared items (required if shared=True)
            brand: Preferred brand
            price: Price of the item
            notes: Additional notes
            
        Returns:
            Created InventoryItem
        """
        self._log_db_query(
            "insert_one",
            payload={
                "name": name,
                "category": category,
                "quantity": quantity,
                "unit": unit,
                "threshold": threshold,
                "user_id": user_id,
                "household_id": household_id,
                "shared": shared,
            },
        )
        item = InventoryItem(
            name=name,
            category=category,
            quantity=quantity,
            unit=unit,
            threshold=threshold,
            expiration_date=expiration_date,
            shared=shared,
            user_id=user_id,
            household_id=household_id,
            brand=brand,
            price=price,
            notes=notes,
        )
        
        await item.insert()
        await self._invalidate_cache()
        logger.info(f"Created inventory item: {name} ({quantity} {unit})")
        return item
    
    @cached_query("inventory", get_inventory_cache)
    async def get_item_by_id(self, item_id: str) -> Optional[InventoryItem]:
        """
        Retrieve an item by its ID.
        
        Args:
            item_id: Unique item identifier
            
        Returns:
            InventoryItem if found, None otherwise
        """
        self._log_db_query("find_one", filters={"item_id": item_id})
        return await InventoryItem.find_one(InventoryItem.item_id == item_id)
    
    @cached_query("inventory", get_inventory_cache)
    async def get_item_by_name(
        self, 
        name: str, 
        user_id: Optional[str] = None,
        household_id: Optional[str] = None
    ) -> Optional[InventoryItem]:
        """
        Retrieve an item by its name, scoped to user or household.
        
        Args:
            name: Item name
            user_id: User ID to filter by (for personal items)
            household_id: Household ID to filter by (for shared items)
            
        Returns:
            InventoryItem if found, None otherwise
        """
        # Build query based on whether it's personal or shared
        if user_id:
            # Personal item: must match user_id and not be shared
            self._log_db_query("find_one", filters={"name": name, "user_id": user_id, "shared": False})
            return await InventoryItem.find_one(
                InventoryItem.name == name,
                InventoryItem.user_id == user_id,
                InventoryItem.shared == False
            )
        elif household_id:
            # Shared item: must match household_id and be shared
            self._log_db_query("find_one", filters={"name": name, "household_id": household_id, "shared": True})
            return await InventoryItem.find_one(
                InventoryItem.name == name,
                InventoryItem.household_id == household_id,
                InventoryItem.shared == True
            )
        else:
            # Fallback: try to find any item with this name (backward compatibility)
            self._log_db_query("find_one", filters={"name": name})
            return await InventoryItem.find_one(InventoryItem.name == name)
    
    async def add_or_increment_item(
        self,
        name: str,
        quantity: float,
        unit: Optional[str] = None,
        category: Optional[str] = None,
        threshold: Optional[float] = None,
        user_id: Optional[str] = None,
        household_id: Optional[str] = None,
        shared: Optional[bool] = None,
    ) -> InventoryItem:
        """
        Ensure an item exists in inventory and increase its quantity.

        Args:
            name: Item name
            quantity: Quantity to add
            unit: Unit of measurement (default: "unit")
            category: Category to assign for new items (default: "General")
            threshold: Low-stock threshold for new items (default: 1.0)
            user_id: User ID for personal items
            household_id: Household ID for shared items
            shared: Whether item is shared (defaults to True if household_id provided, False if user_id provided)

        Returns:
            Updated or created InventoryItem
        """
        unit = unit or "unit"
        category = category or "General"
        quantity = float(quantity)
        threshold = threshold if threshold is not None else max(quantity * 0.2, 1.0)
        
        # Determine shared status if not explicitly provided
        if shared is None:
            if household_id:
                shared = True
            elif user_id:
                shared = False
            else:
                shared = True  # Default to shared for backward compatibility

        existing = await self.get_item_by_name(name, user_id=user_id, household_id=household_id)
        if existing:
            logger.info(
                f"Incrementing inventory for {name}: +{quantity} {unit} (existing {existing.quantity})"
            )
            updated = await self.update_quantity(existing.item_id, quantity)
            return updated or existing

        logger.info(
            f"Creating new inventory item {name} with quantity {quantity} {unit}"
        )
        return await self.create_item(
            name=name,
            category=category,
            quantity=quantity,
            unit=unit,
            threshold=threshold,
            user_id=user_id,
            household_id=household_id,
            shared=shared,
        )

    @cached_query("inventory", get_inventory_cache)
    async def get_all_items(
        self, 
        user_id: Optional[str] = None,
        household_id: Optional[str] = None
    ) -> List[InventoryItem]:
        """
        Retrieve inventory items for a user or household.
        
        If user_id is provided, returns:
        - All personal items for that user (shared=False, user_id=user_id)
        - All shared items for that user's household (shared=True, household_id=household_id)
        
        If household_id is provided, returns:
        - All shared items for that household (shared=True, household_id=household_id)
        
        If neither is provided, returns all items (backward compatibility).
        
        Args:
            user_id: User ID to get items for
            household_id: Household ID to get shared items for
            
        Returns:
            List of InventoryItems
        """
        from models.user import User
        from models.household import Household
        
        items = []
        
        if user_id:
            # Get user's household_id if available
            user = await User.find_one(User.user_id == user_id)
            user_household_id = getattr(user, 'household_id', None) if user else None
            
            # Get personal items
            personal_items = await InventoryItem.find(
                InventoryItem.user_id == user_id,
                InventoryItem.shared == False
            ).to_list()
            items.extend(personal_items)
            
            # Get shared items from user's household
            if user_household_id:
                shared_items = await InventoryItem.find(
                    InventoryItem.household_id == user_household_id,
                    InventoryItem.shared == True
                ).to_list()
                items.extend(shared_items)
            
            self._log_db_query("find", filters={"user_id": user_id, "household_id": user_household_id})
        elif household_id:
            # Get shared items for household
            shared_items = await InventoryItem.find(
                InventoryItem.household_id == household_id,
                InventoryItem.shared == True
            ).to_list()
            items.extend(shared_items)
            self._log_db_query("find", filters={"household_id": household_id, "shared": True})
        else:
            # Backward compatibility: return all items
            self._log_db_query("find_all")
            items = await InventoryItem.find_all().to_list()
        
        return items
    
    @cached_query("inventory", get_inventory_cache)
    async def get_items_by_category(
        self, 
        category: str,
        user_id: Optional[str] = None,
        household_id: Optional[str] = None
    ) -> List[InventoryItem]:
        """
        Retrieve items in a specific category, scoped to user or household.
        
        Args:
            category: Category name
            user_id: User ID to filter by
            household_id: Household ID to filter by
            
        Returns:
            List of InventoryItems in the category
        """
        all_items = await self.get_all_items(user_id=user_id, household_id=household_id)
        filtered = [item for item in all_items if item.category == category]
        self._log_db_query("find", filters={"category": category, "user_id": user_id, "household_id": household_id})
        return filtered
    
    async def update_item(
        self,
        item_id: str,
        **kwargs
    ) -> Optional[InventoryItem]:
        """
        Update an inventory item.
        
        Args:
            item_id: Item ID to update
            **kwargs: Fields to update
            
        Returns:
            Updated InventoryItem if found, None otherwise
        """
        item = await self.get_item_by_id(item_id)
        if not item:
            logger.warning(f"Item not found: {item_id}")
            return None
        
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        item.last_updated = datetime.utcnow()
        self._log_db_query(
            "update_one",
            filters={"item_id": item_id},
            updates=kwargs,
        )
        await item.save()
        await self._invalidate_cache()
        logger.info(f"Updated inventory item: {item.name}")
        return item
    
    async def update_quantity(
        self,
        item_id: str,
        delta: float
    ) -> Optional[InventoryItem]:
        """
        Update item quantity by a delta amount.
        
        Args:
            item_id: Item ID
            delta: Amount to add (positive) or remove (negative)
            
        Returns:
            Updated InventoryItem if found, None otherwise
        """
        item = await self.get_item_by_id(item_id)
        if not item:
            logger.warning(f"Item not found: {item_id}")
            return None
        
        item.update_quantity(delta)
        self._log_db_query(
            "update_quantity",
            filters={"item_id": item_id},
            delta=delta,
        )
        await item.save()
        await self._invalidate_cache()
        logger.info(f"Updated quantity for {item.name}: {delta:+.2f} {item.unit} (now: {item.quantity})")
        return item
    
    async def delete_item(self, item_id: str) -> bool:
        """
        Delete an inventory item.
        
        Args:
            item_id: Item ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        item = await self.get_item_by_id(item_id)
        if not item:
            logger.warning(f"Item not found: {item_id}")
            return False
        
        self._log_db_query("delete_one", filters={"item_id": item_id})
        await item.delete()
        await self._invalidate_cache()
        logger.info(f"Deleted inventory item: {item.name}")
        return True
    
    async def get_low_stock_items(
        self,
        user_id: Optional[str] = None,
        household_id: Optional[str] = None
    ) -> List[InventoryItem]:
        """
        Get all items that are below their threshold, scoped to user or household.
        
        Args:
            user_id: User ID to filter by
            household_id: Household ID to filter by
            
        Returns:
            List of low-stock InventoryItems
        """
        all_items = await self.get_all_items(user_id=user_id, household_id=household_id)
        low_stock = [item for item in all_items if item.is_low_stock()]
        logger.info(f"Found {len(low_stock)} low-stock items")
        return low_stock
    
    async def get_expired_items(self) -> List[InventoryItem]:
        """
        Get all items that have expired.
        
        Returns:
            List of expired InventoryItems
        """
        all_items = await self.get_all_items()
        expired = [item for item in all_items if item.is_expired()]
        logger.info(f"Found {len(expired)} expired items")
        return expired
    
    async def get_expiring_soon(self, days: int = 3) -> List[InventoryItem]:
        """
        Get items expiring within the next N days.
        
        Args:
            days: Number of days to check ahead
            
        Returns:
            List of items expiring soon
        """
        from datetime import timedelta
        threshold_date = datetime.utcnow() + timedelta(days=days)
        
        all_items = await self.get_all_items()
        expiring_soon = [
            item for item in all_items
            if item.expiration_date
            and datetime.utcnow() < item.expiration_date <= threshold_date
        ]
        logger.info(f"Found {len(expiring_soon)} items expiring in {days} days")
        return expiring_soon
    
    async def search_items(
        self, 
        query: str,
        user_id: Optional[str] = None,
        household_id: Optional[str] = None
    ) -> List[InventoryItem]:
        """
        Search for items by name (case-insensitive partial match), scoped to user or household.
        
        Args:
            query: Search query
            user_id: User ID to filter by
            household_id: Household ID to filter by
            
        Returns:
            List of matching InventoryItems
        """
        all_items = await self.get_all_items(user_id=user_id, household_id=household_id)
        matches = [
            item for item in all_items
            if query.lower() in item.name.lower()
        ]
        return matches

