"""
Inventory Service - Business logic for inventory management.
"""
from typing import List, Optional
from datetime import datetime
from loguru import logger

from models.inventory import InventoryItem


class InventoryService:
    """
    Service class for managing grocery inventory.
    
    Provides CRUD operations and business logic for inventory items.
    """
    
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
        logger.info(f"Created inventory item: {name} ({quantity} {unit})")
        return item
    
    async def get_item_by_id(self, item_id: str) -> Optional[InventoryItem]:
        """
        Retrieve an item by its ID.
        
        Args:
            item_id: Unique item identifier
            
        Returns:
            InventoryItem if found, None otherwise
        """
        return await InventoryItem.find_one(InventoryItem.item_id == item_id)
    
    async def get_item_by_name(self, name: str) -> Optional[InventoryItem]:
        """
        Retrieve an item by its name.
        
        Args:
            name: Item name
            
        Returns:
            InventoryItem if found, None otherwise
        """
        return await InventoryItem.find_one(InventoryItem.name == name)
    
    async def get_all_items(self) -> List[InventoryItem]:
        """
        Retrieve all inventory items.
        
        Returns:
            List of all InventoryItems
        """
        return await InventoryItem.find_all().to_list()
    
    async def get_items_by_category(self, category: str) -> List[InventoryItem]:
        """
        Retrieve all items in a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of InventoryItems in the category
        """
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
        await item.save()
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
        await item.save()
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
        
        await item.delete()
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

