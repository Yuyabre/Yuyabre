"""
Core Agent - Central AI orchestrator for the grocery management system.
"""
import copy
import json
from typing import Any, Dict, List, Optional
from loguru import logger
from openai import AsyncOpenAI

from config import settings
from modules.inventory import InventoryService
from modules.splitwise import SplitwiseService
from modules.ordering import OrderingService
from modules.whatsapp import WhatsAppService
from agent.prompts import SYSTEM_PROMPT
from agent.tools import build_tool_specs
from agent.context import build_system_prompt_with_context
from agent.conversation import ConversationManager
from agent.tool_handlers import ToolHandlers


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
        self.whatsapp_service = WhatsAppService()
        base_url = settings.normalized_openai_base_url
        self.openai_client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=base_url,
        )

        logger.info("Grocery Agent initialized")

        self.system_prompt = SYSTEM_PROMPT
        self.tool_specs = build_tool_specs()
        
        # Initialize tool handlers
        self.tool_handlers_obj = ToolHandlers(
            inventory_service=self.inventory_service,
            ordering_service=self.ordering_service,
            splitwise_service=self.splitwise_service,
            whatsapp_service=self.whatsapp_service,
            update_system_prompt_callback=self._update_system_prompt_for_user,
        )
        
        # Map tool names to handler methods
        self.tool_handlers = {
            "get_inventory_snapshot": self.tool_handlers_obj.get_inventory_snapshot,
            "add_inventory_items": self.tool_handlers_obj.add_inventory_items,
            "place_order": self.tool_handlers_obj.place_order,
            "check_low_stock": self.tool_handlers_obj.check_low_stock,
            "get_recent_orders": self.tool_handlers_obj.get_recent_orders,
            "update_user_preferences": self.tool_handlers_obj.update_user_preferences,
            "get_user_info": self.tool_handlers_obj.get_user_info,
            "update_inventory_item": self.tool_handlers_obj.update_inventory_item,
            "send_whatsapp_message": self.tool_handlers_obj.send_whatsapp_message,
        }

        # Initialize conversation manager
        self.conversation_manager = ConversationManager(
            openai_client=self.openai_client,
            tool_specs=self.tool_specs,
            execute_tool=self._execute_tool,
        )

        self.conversations: Dict[str, List[Dict[str, str]]] = {}

    async def _update_system_prompt_for_user(self, user_id: str) -> None:
        """
        Update system prompt for a user and update conversation.
        
        This is used as a callback by tool handlers when preferences change.
        """
        new_prompt = await build_system_prompt_with_context(user_id)
        if user_id in self.conversations:
            self.conversations[user_id][0]["content"] = new_prompt

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
        
        # Build enhanced system prompt with user context
        system_prompt = await build_system_prompt_with_context(user_id)
        
        conversation = self.conversations.setdefault(
            session_id, [{"role": "system", "content": system_prompt}]
        )
        
        # Update system prompt if user context changed
        if conversation[0]["content"] != system_prompt:
            conversation[0]["content"] = system_prompt

        messages = copy.deepcopy(conversation)
        messages.append({"role": "user", "content": command})

        try:
            response_text = await self.conversation_manager.run_conversation(messages, user_id=session_id)
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
        
        # Build enhanced system prompt with user context
        system_prompt = await build_system_prompt_with_context(user_id)
        
        conversation = self.conversations.setdefault(
            session_id, [{"role": "system", "content": system_prompt}]
        )
        
        # Update system prompt if user context changed
        if conversation[0]["content"] != system_prompt:
            conversation[0]["content"] = system_prompt

        messages = copy.deepcopy(conversation)
        messages.append({"role": "user", "content": command})

        full_response = ""
        try:
            async for chunk in self.conversation_manager.run_conversation_stream(messages, user_id=session_id):
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

    async def add_message_to_conversation(
        self, 
        user_id: str, 
        message: str, 
        role: str = "user"
    ) -> None:
        """
        Add a message to a user's conversation context.
        
        This is useful for relaying external messages (e.g., WhatsApp) 
        into the agent's conversation history.
        
        Args:
            user_id: ID of the user
            message: Message content
            role: Message role ("user" or "assistant")
        """
        session_id = user_id or "anonymous"
        
        # Build enhanced system prompt with user context
        system_prompt = await build_system_prompt_with_context(user_id)
        
        conversation = self.conversations.setdefault(
            session_id, [{"role": "system", "content": system_prompt}]
        )
        
        # Update system prompt if user context changed
        if conversation[0]["content"] != system_prompt:
            conversation[0]["content"] = system_prompt
        
        # Add the message to conversation
        conversation.append({"role": role, "content": message})
        
        # Prevent conversation history from growing indefinitely
        if len(conversation) > 20:
            # Keep system prompt plus the last 18 messages (9 exchanges)
            trimmed = [conversation[0]] + conversation[-18:]
            self.conversations[session_id] = trimmed
        
        logger.info(f"Added {role} message to conversation for user {user_id}: {message[:50]}...")

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
