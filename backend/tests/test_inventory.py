"""
Tests for inventory module.
"""
import pytest
from modules.inventory import InventoryService


@pytest.mark.asyncio
async def test_create_inventory_item(test_db):
    """Test creating an inventory item."""
    service = InventoryService()
    
    item = await service.create_item(
        name="Milk",
        category="Dairy",
        quantity=2.0,
        unit="liters",
    )
    
    assert item.name == "Milk"
    assert item.quantity == 2.0
    assert item.unit == "liters"


@pytest.mark.asyncio
async def test_update_quantity(test_db, sample_inventory_item):
    """Test updating item quantity."""
    service = InventoryService()
    
    updated = await service.update_quantity(sample_inventory_item.item_id, 3.0)
    
    assert updated is not None
    assert updated.quantity == 5.0  # 2.0 + 3.0


@pytest.mark.asyncio
async def test_low_stock_detection(test_db, sample_inventory_item):
    """Test low stock detection."""
    service = InventoryService()
    
    # Reduce quantity below threshold
    await service.update_quantity(sample_inventory_item.item_id, -1.5)
    
    low_stock = await service.get_low_stock_items()
    
    assert len(low_stock) > 0
    assert any(item.item_id == sample_inventory_item.item_id for item in low_stock)


@pytest.mark.asyncio
async def test_delete_item(test_db, sample_inventory_item):
    """Test deleting an inventory item."""
    service = InventoryService()
    
    success = await service.delete_item(sample_inventory_item.item_id)
    
    assert success is True
    
    # Verify item is deleted
    item = await service.get_item_by_id(sample_inventory_item.item_id)
    assert item is None

