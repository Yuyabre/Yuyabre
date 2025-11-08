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
    async def get_item_by_name(self, name: str) -> Optional[InventoryItem]:
        """
        Retrieve an item by its name.
        
        Args:
            name: Item name
            
        Returns:
            InventoryItem if found, None otherwise
        """
        self._log_db_query("find_one", filters={"name": name})
        return await InventoryItem.find_one(InventoryItem.name == name)
    
    async def add_or_increment_item(
        self,
        name: str,
        quantity: float,
        unit: Optional[str] = None,
        category: Optional[str] = None,
        threshold: Optional[float] = None,
    ) -> InventoryItem:
        """
        Ensure an item exists in inventory and increase its quantity.

        Args:
            name: Item name
            quantity: Quantity to add
            unit: Unit of measurement (default: "unit")
            category: Category to assign for new items (default: "General")
            threshold: Low-stock threshold for new items (default: 1.0)

        Returns:
            Updated or created InventoryItem
        """
        unit = unit or "unit"
        category = category or "General"
        quantity = float(quantity)
        threshold = threshold if threshold is not None else max(quantity * 0.2, 1.0)

        existing = await self.get_item_by_name(name)
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
        )

    @cached_query("inventory", get_inventory_cache)
    async def get_all_items(self) -> List[InventoryItem]:
        """
        Retrieve all inventory items.
        
        Returns:
            List of all InventoryItems
        """
        self._log_db_query("find_all")
        return await InventoryItem.find_all().to_list()
    
    @cached_query("inventory", get_inventory_cache)
    async def get_items_by_category(self, category: str) -> List[InventoryItem]:
        """
        Retrieve all items in a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of InventoryItems in the category
        """
        self._log_db_query("find", filters={"category": category})
        return await InventoryItem.find(InventoryItem.category == category).to_list()
    
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
    
    async def get_low_stock_items(self) -> List[InventoryItem]:
        """
        Get all items that are below their threshold.
        
        Returns:
            List of low-stock InventoryItems
        """
        all_items = await self.get_all_items()
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
    
    async def search_items(self, query: str) -> List[InventoryItem]:
        """
        Search for items by name (case-insensitive partial match).
        
        Args:
            query: Search query
            
        Returns:
            List of matching InventoryItems
        """
        all_items = await self.get_all_items()
        matches = [
            item for item in all_items
            if query.lower() in item.name.lower()
        ]
        return matches

