"""
Controller for agent-related operations.
"""
from fastapi import HTTPException, status
from loguru import logger

from api.dependencies import agent
from api.serializers import CommandRequest, CommandResponse


class AgentController:
    """Controller for handling agent commands."""
    
    @staticmethod
    async def process_command(request: CommandRequest) -> CommandResponse:
        """
        Process a natural language command through the agent.
        
        Args:
            request: Command request containing the command and optional user_id
            
        Returns:
            CommandResponse with success status and message
            
        Raises:
            HTTPException: If command processing fails
        """
        try:
            response = await agent.process_command(request.command, request.user_id)
            return CommandResponse(success=True, message=response)
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @staticmethod
    async def process_command_stream(request: CommandRequest):
        """
        Process a natural language command through the agent with streaming response.
        
        Args:
            request: Command request containing the command and optional user_id
            
        Yields:
            Chunks of the response text as they become available
            
        Raises:
            HTTPException: If command processing fails
        """
        try:
            async for chunk in agent.process_command_stream(request.command, request.user_id):
                yield chunk
        except Exception as e:
            logger.error(f"Error processing command (streaming): {e}")
            error_message = (
                "I ran into an unexpected issue while trying to help. "
                "Please try again in a moment."
            )
            yield error_message

