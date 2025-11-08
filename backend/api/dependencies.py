"""
Shared dependencies for API routes.

Provides service instances that can be injected into route handlers.
"""
from agent.core import GroceryAgent
from modules.inventory import InventoryService
from modules.ordering import OrderingService
from modules.splitwise import SplitwiseService

# Initialize services as singletons
agent = GroceryAgent()
inventory_service = InventoryService()
ordering_service = OrderingService()
splitwise_service = SplitwiseService()

