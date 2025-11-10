"""
Database initialization and connection management for MongoDB.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from loguru import logger

from config import settings
from models import (
    InventoryItem,
    Order,
    User,
    Household,
    UserInventory,
)
from models.store import Store, StoreInventory


class Database:
    """MongoDB database connection manager."""
    
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect(cls):
        """
        Connect to MongoDB and initialize Beanie ODM.
        """
        try:
            cls.client = AsyncIOMotorClient(settings.mongodb_uri)
            
            # Initialize Beanie with document models
            await init_beanie(
                database=cls.client[settings.mongodb_db_name],
                document_models=[
                    InventoryItem,
                    Order,
                    User,
                    Household,
                    UserInventory,
                    Store,
                    StoreInventory,
                ]
            )
            
            logger.info(f"Connected to MongoDB: {settings.mongodb_db_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close(cls):
        """
        Close MongoDB connection.
        """
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")
    
    @classmethod
    async def ping(cls) -> bool:
        """
        Check if database connection is alive.
        
        Returns:
            True if connection is alive, False otherwise
        """
        try:
            await cls.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database ping failed: {e}")
            return False


# Database instance
db = Database()

