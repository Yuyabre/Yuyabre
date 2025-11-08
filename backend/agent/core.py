"""
Core Agent - Central AI orchestrator for the grocery management system.
"""

import copy
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger
from openai import AsyncOpenAI

from config import settings
from modules.inventory import InventoryService
from modules.splitwise import SplitwiseService
from modules.ordering import OrderingService
from models.order import OrderStatus
from agent.prompts import SYSTEM_PROMPT
from agent.tools import build_tool_specs


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

        self.system_prompt = SYSTEM_PROMPT
        self.tool_specs = build_tool_specs()
        self.tool_handlers = {
            "get_inventory_snapshot": self._tool_get_inventory_snapshot,
            "add_inventory_items": self._tool_add_inventory_items,
            "place_order": self._tool_place_order,
            "check_low_stock": self._tool_check_low_stock,
            "get_recent_orders": self._tool_get_recent_orders,
        }

        self.conversations: Dict[str, List[Dict[str, str]]] = {}

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

        session_id = user_id or "anonymous"
        conversation = self.conversations.setdefault(
            session_id, [{"role": "system", "content": self.system_prompt}]
        )

        messages = copy.deepcopy(conversation)
        messages.append({"role": "user", "content": command})

        try:
            response_text = await self._run_conversation(messages, user_id=session_id)
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            response_text = (
                "I ran into an unexpected issue while trying to help. "
                "Please try again in a moment."
            )

        # Persist the latest exchange for conversational context
        conversation.append({"role": "user", "content": command})
        conversation.append({"role": "assistant", "content": response_text})

        # Prevent conversation history from growing indefinitely
        if len(conversation) > 20:
            # Keep system prompt plus the last 18 messages (9 exchanges)
            trimmed = [conversation[0]] + conversation[-18:]
            self.conversations[session_id] = trimmed

        return response_text

    async def process_command_stream(
        self, command: str, user_id: Optional[str] = None
    ):
        """
        Process a natural language command from the user with streaming response.

        Args:
            command: User's text command
            user_id: ID of the user issuing the command

        Yields:
            Chunks of the response text as they become available
        """
        logger.info(f"Processing command (streaming): {command}")

        session_id = user_id or "anonymous"
        conversation = self.conversations.setdefault(
            session_id, [{"role": "system", "content": self.system_prompt}]
        )

        messages = copy.deepcopy(conversation)
        messages.append({"role": "user", "content": command})

        full_response = ""
        try:
            async for chunk in self._run_conversation_stream(messages, user_id=session_id):
                full_response += chunk
                yield chunk
        except Exception as e:
            logger.error(f"Error processing command (streaming): {e}")
            error_message = (
                "I ran into an unexpected issue while trying to help. "
                "Please try again in a moment."
            )
            full_response = error_message
            yield error_message

        # Persist the latest exchange for conversational context
        conversation.append({"role": "user", "content": command})
        conversation.append({"role": "assistant", "content": full_response})

        # Prevent conversation history from growing indefinitely
        if len(conversation) > 20:
            # Keep system prompt plus the last 18 messages (9 exchanges)
            trimmed = [conversation[0]] + conversation[-18:]
            self.conversations[session_id] = trimmed

    async def _run_conversation(
        self, messages: List[Dict[str, Any]], user_id: Optional[str] = None
    ) -> str:
        """
        Drive the multi-turn LLM conversation with tool usage.
        """
        logger.debug(f"Running conversation with messages: {messages}")
        while True:
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                tools=self.tool_specs,
                tool_choice="auto",
            )

            message = response.choices[0].message
            logger.debug(f"Response from core agent: {message}")
            tool_calls = getattr(message, "tool_calls", None)

            if tool_calls:
                # Record the assistant tool call message
                messages.append(message.model_dump())

                for tool_call in tool_calls:
                    tool_result = await self._execute_tool(tool_call, user_id=user_id)
                    logger.debug(f"Tool result: {tool_result}")
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result, default=str),
                        }
                    )
                continue

            content = message.content or ""
            if not content.strip():
                return "I'm not sure how to answer that right now."
            return content.strip()

    async def _run_conversation_stream(
        self, messages: List[Dict[str, Any]], user_id: Optional[str] = None
    ):
        """
        Drive the multi-turn LLM conversation with tool usage, streaming responses.
        
        Yields:
            Chunks of text as they become available from the LLM
        """
        logger.debug(f"Running conversation (streaming) with messages: {messages}")
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            stream = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                tools=self.tool_specs,
                tool_choice="auto",
                stream=True,
            )

            message_content = ""
            tool_calls_dict = {}  # index -> tool_call data

            async for chunk in stream:
                if not chunk.choices:
                    continue
                    
                delta = chunk.choices[0].delta
                
                # Handle content streaming
                if delta.content:
                    message_content += delta.content
                    yield delta.content
                
                # Handle tool calls (they come in chunks too)
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        if tool_call_delta.index is None:
                            continue
                            
                        idx = tool_call_delta.index
                        if idx not in tool_calls_dict:
                            tool_calls_dict[idx] = {
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            }
                        
                        tc = tool_calls_dict[idx]
                        
                        if tool_call_delta.id:
                            tc["id"] = tool_call_delta.id
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                tc["function"]["name"] = tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                tc["function"]["arguments"] += tool_call_delta.function.arguments

            # Check if we have tool calls to execute
            tool_calls_list = [tc for tc in tool_calls_dict.values() if tc.get("function", {}).get("name")]
            
            if tool_calls_list:
                # Create a mock tool call object for each tool call
                class MockToolCall:
                    def __init__(self, tc_data):
                        self.id = tc_data["id"]
                        self.function = type('obj', (object,), {
                            'name': tc_data["function"]["name"],
                            'arguments': tc_data["function"]["arguments"]
                        })()
                
                # Store assistant message with tool calls
                assistant_msg = {
                    "role": "assistant",
                    "content": message_content if message_content else None,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"]
                            }
                        }
                        for tc in tool_calls_list
                    ]
                }
                messages.append(assistant_msg)
                
                # Execute each tool call
                for tc_data in tool_calls_list:
                    tool_call = MockToolCall(tc_data)
                    
                    # Yield a status message about tool execution
                    tool_name = tc_data["function"]["name"]
                    yield f"\n\n[Executing {tool_name}...]\n\n"
                    
                    # Execute tool
                    tool_result = await self._execute_tool(tool_call, user_id=user_id)
                    logger.debug(f"Tool result: {tool_result}")
                    
                    # Add tool result to messages
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc_data["id"],
                            "content": json.dumps(tool_result, default=str),
                        }
                    )
                continue

            # If we have content, we're done with this turn
            if message_content.strip():
                # Store the assistant's message
                messages.append({
                    "role": "assistant",
                    "content": message_content
                })
                return
            
            # If no content and no tool calls, something went wrong
            if not message_content.strip() and not tool_calls_list:
                yield "I'm not sure how to answer that right now."
                return

    async def _execute_tool(
        self, tool_call, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool requested by the LLM.
        """
        name = tool_call.function.name
        raw_arguments = tool_call.function.arguments or "{}"

        try:
            logger.debug(f"Executing tool: {name} with arguments: {raw_arguments}")
            arguments = json.loads(raw_arguments) if raw_arguments else {}
        except json.JSONDecodeError:
            logger.error(f"Failed to decode tool arguments for {name}: {raw_arguments}")
            return {"error": f"Invalid arguments for tool {name}."}

        handler = self.tool_handlers.get(name)
        if not handler:
            logger.error(f"LLM attempted to call unknown tool: {name}")
            return {"error": f"Tool {name} is not implemented."}

        try:
            result = await handler(user_id=user_id, **arguments)
            return {"result": result}
        except Exception as exc:
            logger.error(f"Tool {name} failed: {exc}")
            return {"error": f"Tool {name} failed with error: {exc}"}

    async def _tool_get_inventory_snapshot(
        self,
        user_id: Optional[str] = None,
        dish: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return a snapshot of current inventory, optionally filtered.
        """
        items = await self.inventory_service.get_all_items()

        def matches_query(item) -> bool:
            if search and search.lower() not in item.name.lower():
                return False
            return True

        filtered = [item for item in items if matches_query(item)]

        return {
            "dish": dish,
            "count": len(filtered),
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "category": item.category,
                    "threshold": item.threshold,
                }
                for item in filtered
            ],
        }

    async def _tool_add_inventory_items(
        self,
        *,
        items: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add or increment items in the inventory.
        """
        if not items:
            return {"error": "No items provided to add."}

        results = []
        for item in items:
            name = item.get("name")
            quantity = item.get("quantity")
            if not name or quantity is None:
                results.append(
                    {
                        "name": name or "unknown",
                        "status": "skipped",
                        "reason": "Missing name or quantity.",
                    }
                )
                continue

            existing_item = await self.inventory_service.get_item_by_name(name)
            updated = await self.inventory_service.add_or_increment_item(
                name=name,
                quantity=quantity,
                unit=item.get("unit"),
                category=item.get("category"),
            )
            results.append(
                {
                    "name": updated.name,
                    "quantity": updated.quantity,
                    "unit": updated.unit,
                    "status": "updated" if existing_item else "created",
                }
            )

        return {"items": results}

    async def _tool_place_order(
        self,
        *,
        items: List[Dict[str, Any]],
        delivery_address: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place an order for the given items.
        """
        if not items:
            return {"error": "No items provided to order."}

        order_items = []
        missing_products = []

        for item in items:
            name = item.get("name")
            quantity = float(item.get("quantity", 0))
            if not name or quantity <= 0:
                missing_products.append(
                    {"name": name, "reason": "Invalid name or quantity"}
                )
                continue

            products = await self.ordering_service.search_products(name)
            if not products:
                missing_products.append(
                    {"name": name, "reason": "No matching products found"}
                )
                continue

            product = products[0]
            order_items.append(
                {
                    "product_id": product["product_id"],
                    "name": product["name"],
                    "quantity": quantity,
                    "unit": item.get("unit") or product.get("unit") or "unit",
                    "price": product["price"],
                    "requested_by": [user_id] if user_id else [],
                }
            )

        if not order_items:
            return {
                "error": "No products could be matched for ordering.",
                "missing": missing_products,
            }

        order = await self.ordering_service.create_order(
            items=order_items,
            delivery_address=delivery_address or "Default Address",
            notes=notes,
            created_by=user_id,
        )

        if not order:
            return {"error": "Failed to create the order with the delivery service."}

        # Update inventory with ordered items
        for item in order.items:
            await self.inventory_service.add_or_increment_item(
                name=item.name,
                quantity=item.quantity,
                unit=item.unit,
                category="Ordered",
            )

        summary = {
            "order_id": order.order_id,
            "status": order.status.value,
            "total": order.total,
            "items": [
                {
                    "name": it.name,
                    "quantity": it.quantity,
                    "unit": it.unit,
                    "price": it.price,
                }
                for it in order.items
            ],
        }

        if missing_products:
            summary["partial_warnings"] = missing_products

        return summary

    async def _tool_check_low_stock(
        self,
        *,
        limit: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List low-stock items.
        """
        items = await self.inventory_service.get_low_stock_items()
        if limit:
            items = items[:limit]

        return {
            "count": len(items),
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "threshold": item.threshold,
                }
                for item in items
            ],
        }

    async def _tool_get_recent_orders(
        self,
        *,
        limit: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve recent orders.
        """
        orders = await self.ordering_service.get_order_history(limit=limit or 5)
        return {
            "count": len(orders),
            "orders": [
                {
                    "order_id": order.order_id,
                    "status": order.status.value,
                    "total": order.total,
                    "created_at": order.timestamp.isoformat(),
                    "items": [
                        {
                            "name": item.name,
                            "quantity": item.quantity,
                            "unit": item.unit,
                        }
                        for item in order.items
                    ],
                }
                for order in orders
            ],
        }

    async def _parse_intent(self, command: str) -> Dict:
        """
        Use LLM to parse user intent from natural language.

        Args:
            command: User's text command

        Returns:
            Dictionary with parsed intent and parameters
        """
        system_prompt = """You are a grocery management assistant. Parse user commands and extract:
                        1. Action: order, inventory_add, inventory_query, inventory_update, order_status, low_stock, undefined
                        2. Parameters: item names, quantities, units, etc.

                        Respond strictly with JSON only, no explanation. Format:
                        {
                            "action": "order|inventory_add|inventory_query|inventory_update|order_status|low_stock|undefined",
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
            word in command_lower
            for word in [
                "what",
                "show",
                "list",
                "inventory",
                "enough",
                "do i have",
                "have enough",
            ]
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
        items = intent.get("items", []) or []

        if not items:
            inferred_items = await self._infer_order_items_from_query(
                intent.get("query", "")
            )
            items.extend(inferred_items)

        if not items:
            return (
                "I couldn't identify what items to order. "
                "Please specify item names and quantities."
            )

        stock_fulfilled: List[Dict] = []
        stock_partial: List[Dict] = []
        order_candidates: List[Dict] = []

        for item in items:
            name = item.get("name")
            if not name:
                continue

            required_quantity = float(item.get("quantity") or 1)
            unit = item.get("unit") or "unit"

            inventory_item = await self._find_inventory_item(name)
            available_quantity = (
                float(inventory_item.quantity) if inventory_item else 0.0
            )

            if inventory_item and available_quantity >= required_quantity:
                stock_fulfilled.append(
                    {
                        "name": inventory_item.name,
                        "quantity": available_quantity,
                        "unit": inventory_item.unit,
                    }
                )
                continue

            missing_quantity = max(required_quantity - available_quantity, 0.0)
            if missing_quantity <= 0:
                stock_fulfilled.append(
                    {
                        "name": name,
                        "quantity": available_quantity,
                        "unit": unit,
                    }
                )
                continue

            if inventory_item and available_quantity > 0:
                stock_partial.append(
                    {
                        "name": inventory_item.name,
                        "required": required_quantity,
                        "available": available_quantity,
                        "unit": inventory_item.unit,
                    }
                )

            order_candidates.append(
                {
                    "name": name,
                    "quantity": missing_quantity,
                    "unit": unit,
                }
            )

        if not order_candidates:
            if stock_fulfilled or stock_partial:
                response_lines = ["Inventory already has the ingredients you need:"]
                for item in stock_fulfilled:
                    response_lines.append(
                        f"- {item['name']}: {item['quantity']} {item['unit']}"
                    )
                for item in stock_partial:
                    response_lines.append(
                        f"- {item['name']}: {item['available']} {item['unit']} available "
                        f"(needed {item['required']} {item['unit']})"
                    )
                return "\n".join(response_lines)

            return (
                "I couldn't identify what items to order. "
                "Please specify item names and quantities."
            )

        order_items = []
        for item in order_candidates:
            products = await self.ordering_service.search_products(item["name"])
            if not products:
                logger.warning(f"No products found for {item['name']}")
                continue

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
            return "I couldn't find any matching products for the items you need."

        order = await self.ordering_service.create_order(
            items=order_items,
            delivery_address="Default Address",  # TODO: Get from user profile
            created_by=user_id,
        )

        if not order:
            return "Failed to create order. Please try again."

        for item in order.items:
            await self.inventory_service.add_or_increment_item(
                name=item.name,
                quantity=item.quantity,
                unit=item.unit,
                category="Ordered",
            )

        if self.splitwise_service.is_configured():
            expense_id = await self.splitwise_service.create_expense(
                description=f"Grocery Order - {order.service}",
                amount=order.total,
                user_ids=["123"],  # TODO: Get actual user IDs from flatmates
                notes=f"Order ID: {order.order_id}",
            )

            if expense_id:
                order.splitwise_expense_id = expense_id
                await order.save()

        response_lines = [
            "✓ Order placed successfully!",
            f"Order ID: {order.order_id}",
            f"Items ordered: {len(order.items)}",
            f"Total: €{order.total:.2f}",
            f"Status: {order.status.value}",
        ]

        if stock_fulfilled:
            response_lines.append("Already in stock:")
            response_lines.extend(
                f"- {item['name']}: {item['quantity']} {item['unit']}"
                for item in stock_fulfilled
            )

        if stock_partial:
            response_lines.append("Partially in stock:")
            response_lines.extend(
                f"- {item['name']}: {item['available']} {item['unit']} available "
                f"(ordered {item['required'] - item['available']:.2f} {item['unit']})"
                for item in stock_partial
            )

        if order.splitwise_expense_id:
            response_lines.append("Splitwise expense created.")

        return "\n".join(response_lines)

    async def _find_inventory_item(self, name: str):
        """Find an inventory item by name using exact or fuzzy matching."""
        item = await self.inventory_service.get_item_by_name(name)
        if item:
            return item

        matches = await self.inventory_service.search_items(name)
        return matches[0] if matches else None

    async def _infer_order_items_from_query(self, query: str) -> List[Dict]:
        """
        Use LLM to infer order items from a natural language query,
        taking current inventory into account.
        """
        if not query:
            return []

        inventory_items = await self.inventory_service.get_all_items()
        inventory_summary = [
            {
                "name": item.name,
                "quantity": item.quantity,
                "unit": item.unit,
            }
            for item in inventory_items
        ]

        system_prompt = (
            "You help plan grocery orders. "
            "Given a cooking request and the current inventory, "
            "list only the items that still need to be ordered. "
            "If nothing needs to be ordered, return an empty list. "
            "Respond strictly as JSON matching this schema:\n"
            '{"order_items": [{"name": "item", "quantity": 1.0, "unit": "pieces"}]}'
        )

        user_payload = json.dumps(
            {
                "request": query,
                "inventory": inventory_summary,
            }
        )

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"User request and inventory:\n{user_payload}",
                    },
                ],
            )

            parsed = json.loads(response.choices[0].message.content)
            items = parsed.get("order_items", [])
            cleaned_items = []
            for item in items:
                name = item.get("name")
                if not name:
                    continue
                cleaned_items.append(
                    {
                        "name": name,
                        "quantity": float(item.get("quantity", 1) or 1),
                        "unit": item.get("unit") or "unit",
                    }
                )
            return cleaned_items
        except Exception as e:
            logger.error(f"Failed to infer order items from query: {e}")
            return []

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
        inventory_items = await self.inventory_service.get_all_items()

        if "low" in query.lower():
            items = await self.inventory_service.get_low_stock_items()
            if not items:
                return "All items are well-stocked!"
            return "Low stock items:\n" + "\n".join(
                f"- {item.name}: {item.quantity} {item.unit} (threshold: {item.threshold})"
                for item in items
            )

        if any(
            phrase in query.lower() for phrase in ["enough", "do i have", "have enough"]
        ):
            if not inventory_items:
                return (
                    "Looks like your inventory is empty right now. "
                    "Want me to order the ingredients for you?"
                )

            return "Yes! You already have what you need:\n" + "\n".join(
                f"- {item.name}: {item.quantity} {item.unit}"
                for item in inventory_items
            )

        if not inventory_items:
            return "Inventory is empty."

        return "Current inventory:\n" + "\n".join(
            f"- {item.name}: {item.quantity} {item.unit}" for item in inventory_items
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
