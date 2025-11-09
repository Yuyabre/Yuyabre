"""
Conversation Management - Handling LLM conversations with tool usage.
"""
import json
from typing import Any, Dict, List, Optional, Callable, Awaitable
from loguru import logger
from openai import AsyncOpenAI

from config import settings


class ConversationManager:
    """
    Manages LLM conversations with tool usage support.
    """
    
    def __init__(
        self,
        openai_client: AsyncOpenAI,
        tool_specs: List[Dict[str, Any]],
        execute_tool: Callable[[Any, Optional[str]], Awaitable[Dict[str, Any]]],
    ):
        """
        Initialize conversation manager.
        
        Args:
            openai_client: OpenAI client for API calls
            tool_specs: List of tool specifications
            execute_tool: Function to execute tools
        """
        self.openai_client = openai_client
        self.tool_specs = tool_specs
        self.execute_tool = execute_tool
    
    async def run_conversation(
        self, messages: List[Dict[str, Any]], user_id: Optional[str] = None
    ) -> str:
        """
        Drive the multi-turn LLM conversation with tool usage.
        
        Args:
            messages: Conversation messages
            user_id: Optional user ID for tool execution
            
        Returns:
            Final response text
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
                    tool_result = await self.execute_tool(tool_call, user_id=user_id)
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

    async def run_conversation_stream(
        self, messages: List[Dict[str, Any]], user_id: Optional[str] = None
    ):
        """
        Drive the multi-turn LLM conversation with tool usage, streaming responses.
        
        Args:
            messages: Conversation messages
            user_id: Optional user ID for tool execution
            
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
                    tool_result = await self.execute_tool(tool_call, user_id=user_id)
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

