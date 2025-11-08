"""
Database initialization script.

Run this script to set up initial data and test the database connection.
"""
import asyncio
from loguru import logger

from database import db
from modules.inventory import InventoryService


async def init_sample_data():
    """Initialize database with sample data."""
    logger.info("Initializing database with sample data...")
    
    # Connect to database
    await db.connect()
    
    # Create inventory service
    inventory_service = InventoryService()
    
    # Add sample inventory items
    sample_items = [
        {
            "name": "Milk",
            "category": "Dairy",
            "quantity": 2.0,
            "unit": "liters",
            "threshold": 1.0,
            "shared": True,
            "price": 1.79,
        },
        {
            "name": "Eggs",
            "category": "Dairy",
            "quantity": 12.0,
            "unit": "pieces",
            "threshold": 6.0,
            "shared": True,
            "price": 3.49,
        },
        {
            "name": "Bread",
            "category": "Bakery",
            "quantity": 1.0,
            "unit": "loaf",
            "threshold": 1.0,
            "shared": True,
            "price": 2.29,
        },
        {
            "name": "Cheese",
            "category": "Dairy",
            "quantity": 0.5,
            "unit": "kg",
            "threshold": 0.3,
            "shared": True,
            "price": 6.99,
        },
        {
            "name": "Tomatoes",
            "category": "Vegetables",
            "quantity": 1.0,
            "unit": "kg",
            "threshold": 0.5,
            "shared": True,
            "price": 2.99,
        },
    ]
    
    for item_data in sample_items:
        try:
            item = await inventory_service.create_item(**item_data)
            logger.info(f"Created: {item.name}")
        except Exception as e:
            logger.error(f"Failed to create {item_data['name']}: {e}")
    
    logger.info("Database initialization complete!")
    
    # Close connection
    await db.close()


async def check_connection():
    """Check database connection."""
    logger.info("Checking database connection...")
    
    await db.connect()
    
    is_connected = await db.ping()
    if is_connected:
        logger.info("✓ Database connection successful!")
    else:
        logger.error("✗ Database connection failed!")
    
    await db.close()


async def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            await check_connection()
        elif command == "init":
            await init_sample_data()
        else:
            print("Unknown command. Use 'check' or 'init'")
    else:
        print("Usage:")
        print("  python scripts/init_db.py check  - Check database connection")
        print("  python scripts/init_db.py init   - Initialize with sample data")


if __name__ == "__main__":
    asyncio.run(main())

