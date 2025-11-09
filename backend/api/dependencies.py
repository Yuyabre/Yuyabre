"""
Shared dependencies for API routes.

Provides service instances that can be injected into route handlers.
"""
from agent.core import GroceryAgent
from modules.inventory import InventoryService
from modules.ordering import OrderingService
from modules.splitwise import SplitwiseService
from modules.user import UserService
from modules.discord import DiscordService

# Initialize services as singletons
agent = GroceryAgent()
inventory_service = InventoryService()
ordering_service = OrderingService()
splitwise_service = SplitwiseService()
user_service = UserService()
discord_service = DiscordService()  # Shared Discord service instance for bot and messaging

