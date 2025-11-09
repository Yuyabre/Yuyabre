"""
Core Agent - Central AI orchestrator for the grocery management system.
"""
import json
from typing import Optional, Dict, List
from datetime import datetime
from loguru import logger
from openai import AsyncOpenAI

from config import settings
from modules.inventory import InventoryService
from modules.splitwise import SplitwiseService
from modules.ordering import OrderingService
from models.order import OrderStatus
from models.user import User


class GroceryAgent:
    """
    Central AI agent that orchestrates grocery management operations.

    The agent processes natural language commands, makes decisions, and
    coordinates between inventory, ordering, and expense splitting.
    """

    def __init__(self):
        """Initialize the agent and all service modules."""
        self.inventory_service = InventoryService()
        self.splitwise_service = SplitwiseService()
        self.ordering_service = OrderingService()
        base_url = settings.normalized_openai_base_url
        self.openai_client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=base_url,
        )

        logger.info("Grocery Agent initialized")

    async def process_command(self, command: str, user_id: Optional[str] = None) -> str:
        """
        Process a natural language command from the user.

        Args:
            command: User's text command
            user_id: ID of the user issuing the command

        Returns:
            Response text from the agent
        """
        logger.info(f"Processing command: {command}")

        try:
            # Use LLM to understand the intent
            intent = await self._parse_intent(command)

            # Route to appropriate handler
            if intent["action"] == "order":
                return await self._handle_order(intent, user_id)
            elif intent["action"] == "inventory_add":
                return await self._handle_inventory_add(intent)
            elif intent["action"] == "inventory_query":
                return await self._handle_inventory_query(intent)
            elif intent["action"] == "inventory_update":
                return await self._handle_inventory_update(intent)
            elif intent["action"] == "order_status":
                return await self._handle_order_status(intent)
            elif intent["action"] == "low_stock":
                return await self._handle_low_stock_check()
            else:
                return "I'm not sure how to help with that. Try asking about ordering, checking inventory, or order status."

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

    async def _parse_intent(self, command: str) -> Dict:
        """
        Use LLM to parse user intent from natural language.

        Args:
            command: User's text command

        Returns:
            Dictionary with parsed intent and parameters
        """
        system_prompt = """You are a grocery management assistant. Parse user commands and extract:
                        1. Action: order, inventory_add, inventory_query, inventory_update, order_status, low_stock
                        2. Parameters: item names, quantities, units, etc.

                        Respond with JSON only, no explanation. Format:
                        {
                            "action": "order|inventory_add|inventory_query|inventory_update|order_status|low_stock",
                            "items": [{"name": "item", "quantity": 2, "unit": "liters"}],
                            "query": "search query if applicable"
                        }"""

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": command},
                ],
                temperature=0.3,
            )

            intent = json.loads(response.choices[0].message.content)
            logger.debug(f"Parsed intent: {intent}")
            return intent

        except Exception as e:
            logger.error(f"Failed to parse intent: {e}")
            # Fallback to simple keyword matching
            return self._simple_intent_parse(command)

    def _simple_intent_parse(self, command: str) -> Dict:
        """Fallback simple intent parsing using keywords."""
        command_lower = command.lower()

        if any(word in command_lower for word in ["order", "buy", "purchase"]):
            return {"action": "order", "items": [], "query": command}
        elif any(word in command_lower for word in ["add", "bought"]):
            return {"action": "inventory_add", "items": [], "query": command}
        elif any(
            word in command_lower for word in ["what", "show", "list", "inventory"]
        ):
            return {"action": "inventory_query", "query": command}
        elif "status" in command_lower:
            return {"action": "order_status", "query": command}
        elif "low stock" in command_lower:
            return {"action": "low_stock"}
        else:
            return {"action": "unknown", "query": command}

    async def _handle_order(self, intent: Dict, user_id: Optional[str]) -> str:
        """Handle order placement request."""
        items = intent.get("items", [])

        if not items:
            return "I couldn't identify what items to order. Please specify item names and quantities."

        # Search for products and create order
        order_items = []
        for item in items:
            products = await self.ordering_service.search_products(item["name"])
            if products:
                order_items.append(
                    {
                        "product_id": products[0]["product_id"],
                        "name": products[0]["name"],
                        "quantity": item.get("quantity", 1),
                        "unit": item.get("unit", "piece"),
                        "price": products[0]["price"],
                        "requested_by": [user_id] if user_id else [],
                    }
                )

        if not order_items:
            return "I couldn't find any matching products for your order."

        # Create order
        order = await self.ordering_service.create_order(
            items=order_items,
            delivery_address="Default Address",  # TODO: Get from user profile
            created_by=user_id,
        )

        if not order:
            return "Failed to create order. Please try again."

        # Update inventory (assuming order will be delivered)
        for item in order.items:
            inventory_item = await self.inventory_service.get_item_by_name(item.name)
            if inventory_item:
                await self.inventory_service.update_quantity(
                    inventory_item.item_id, item.quantity
                )

        # # Create Splitwise expense using direct API calls
        # if self.splitwise_service.is_configured() and user_id:
        #     # Check if user is authorized
        #     if await self.splitwise_service.is_user_authorized(user_id):
        #         # TODO: Get actual Splitwise user IDs from flatmates
        #         # For now, we'll need the user's own Splitwise user ID
        #         user = await User.find_one(User.user_id == user_id)
        #         if user and user.splitwise_user_id and user.splitwise_access_token:
        #             try:
        #                 import requests
        #                 from requests_oauthlib import OAuth1
                        
        #                 # Create OAuth session
        #                 session = requests.Session()
        #                 session.auth = OAuth1(
        #                     self.splitwise_service.consumer_key,
        #                     client_secret=self.splitwise_service.consumer_secret,
        #                     resource_owner_key=user.splitwise_access_token,
        #                     resource_owner_secret=user.splitwise_access_token_secret
        #                 )
                        
        #                 # Build expense data
        #                 expense_data = {
        #                     "cost": str(round(order.total, 2)),
        #                     "description": f"Grocery Order - {order.service}",
        #                     "currency_code": "EUR",
        #                     "users[0][user_id]": str(int(user.splitwise_user_id)),
        #                     "users[0][paid_share]": str(round(order.total, 2)),
        #                     "users[0][owed_share]": str(round(order.total, 2)),
        #                 }
                        
        #                 # Make API call
        #                 response = session.post(
        #                     'https://secure.splitwise.com/api/v3.0/create_expense',
        #                     data=expense_data,
        #                     headers={'Content-Type': 'application/x-www-form-urlencoded'}
        #                 )
                        
        #                 if response.status_code == 200:
        #                     result = response.json()
        #                     if 'expenses' in result and len(result['expenses']) > 0:
        #                         expense_id = str(result['expenses'][0]['id'])
        #                         order.splitwise_expense_id = expense_id
        #                         await order.save()
        #             except Exception as e:
        #                 logger.warning(f"Failed to create Splitwise expense: {e}")

        return (
            f"✓ Order placed successfully!\n"
            f"Order ID: {order.order_id}\n"
            f"Items: {len(order.items)}\n"
            f"Total: €{order.total:.2f}\n"
            f"Status: {order.status.value}\n"
            f"{'Splitwise expense created.' if order.splitwise_expense_id else ''}"
        )

    async def _handle_inventory_add(self, intent: Dict) -> str:
        """Handle adding items to inventory."""
        items = intent.get("items", [])

        if not items:
            return "Please specify what items to add to inventory."

        added = []
        for item in items:
            inventory_item = await self.inventory_service.create_item(
                name=item["name"],
                category=item.get("category", "General"),
                quantity=item.get("quantity", 1),
                unit=item.get("unit", "piece"),
            )
            added.append(
                f"{inventory_item.name} ({inventory_item.quantity} {inventory_item.unit})"
            )

        return f"✓ Added to inventory:\n" + "\n".join(f"- {item}" for item in added)

    async def _handle_inventory_query(self, intent: Dict) -> str:
        """Handle inventory queries."""
        query = intent.get("query", "")

        if "low" in query.lower():
            items = await self.inventory_service.get_low_stock_items()
            if not items:
                return "All items are well-stocked!"
            return "Low stock items:\n" + "\n".join(
                f"- {item.name}: {item.quantity} {item.unit} (threshold: {item.threshold})"
                for item in items
            )

        # General inventory list
        items = await self.inventory_service.get_all_items()
        if not items:
            return "Inventory is empty."

        return "Current inventory:\n" + "\n".join(
            f"- {item.name}: {item.quantity} {item.unit}" for item in items
        )

    async def _handle_inventory_update(self, intent: Dict) -> str:
        """Handle inventory updates."""
        # TODO: Implement inventory update logic
        return "Inventory update functionality coming soon."

    async def _handle_order_status(self, intent: Dict) -> str:
        """Handle order status queries."""
        orders = await self.ordering_service.get_order_history(limit=5)
        if not orders:
            return "No recent orders found."

        return "Recent orders:\n" + "\n".join(
            f"- {order.order_id[:8]}: {order.status.value} (€{order.total:.2f})"
            for order in orders
        )

    async def _handle_low_stock_check(self) -> str:
        """Handle low stock check."""
        items = await self.inventory_service.get_low_stock_items()
        if not items:
            return "✓ All items are well-stocked!"

        return "⚠️ Low stock alert:\n" + "\n".join(
            f"- {item.name}: {item.quantity} {item.unit} (need: {item.threshold})"
            for item in items
        )
