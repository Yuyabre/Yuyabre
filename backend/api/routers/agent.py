"""
Router for agent-related endpoints.
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.controllers.agent_controller import AgentController
from api.serializers import CommandRequest, CommandResponse

router = APIRouter(prefix="/agent", tags=["Agent"])

controller = AgentController()


@router.post("/command", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    """
    Process a natural language command through the agent.
    
    The agent will parse the intent and execute the appropriate action.
    """
    return await controller.process_command(request)


@router.post("/command/stream")
async def process_command_stream(request: CommandRequest):
    """
    Process a natural language command through the agent with streaming response.
    
    Returns a Server-Sent Events (SSE) stream of the agent's response.
    The frontend can consume this using EventSource or fetch with ReadableStream.
    """
    async def generate_sse():
        """Generate Server-Sent Events from agent stream."""
        try:
            async for chunk in controller.process_command_stream(request):
                # Format as SSE: data: <content>\n\n
                # Handle newlines by splitting and prefixing each line with "data: "
                if '\n' in chunk:
                    lines = chunk.split('\n')
                    for line in lines[:-1]:  # All but the last line
                        yield f"data: {line}\n"
                    # Last line (might be empty if chunk ends with \n)
                    yield f"data: {lines[-1]}\n\n"
                else:
                    # No newlines, simple case
                    yield f"data: {chunk}\n\n"
            # Send end marker
            yield "data: [DONE]\n\n"
        except Exception as e:
            # Send error as SSE event
            error_msg = f"Error: {str(e)}"
            if '\n' in error_msg:
                lines = error_msg.split('\n')
                for line in lines[:-1]:
                    yield f"data: {line}\n"
                yield f"data: {lines[-1]}\n\n"
            else:
                yield f"data: {error_msg}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        }
    )

