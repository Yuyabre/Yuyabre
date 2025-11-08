"""
Pytest configuration and fixtures.
"""
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from models import InventoryItem, Order, User


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """
    Create a test database connection.
    
    This fixture sets up a clean test database for each test.
    """
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    database = client["grocery_agent_test"]
    
    # Initialize Beanie
    await init_beanie(
        database=database,
        document_models=[InventoryItem, Order, User]
    )
    
    yield database
    
    # Cleanup: drop test database after test
    await client.drop_database("grocery_agent_test")
    client.close()


@pytest.fixture
async def sample_inventory_item(test_db):
    """Create a sample inventory item for testing."""
    item = InventoryItem(
        name="Test Milk",
        category="Dairy",
        quantity=2.0,
        unit="liters",
        threshold=1.0,
        shared=True,
    )
    await item.insert()
    return item

