"""
Router for agent-related endpoints.
"""
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from api.controllers.agent_controller import AgentController
from api.serializers import CommandRequest, CommandResponse
from api.websocket_manager import websocket_manager

router = APIRouter(prefix="/agent", tags=["Agent"])

controller = AgentController()


@router.post("/command", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    """
    Process a natural language command through the agent.
    
    The agent will parse the intent and execute the appropriate action.
    """
    return await controller.process_command(request)


@router.websocket("/command/stream")
async def process_command_stream_websocket(websocket: WebSocket):
    """
    Process a natural language command through the agent with streaming response via WebSocket.
    
    The WebSocket connection:
    - Auto-closes after 5 minutes of inactivity
    - Supports multiple commands per connection
    - Automatically closes when client disconnects (e.g., page refresh)
    
    The frontend should connect to this WebSocket endpoint and send JSON messages:
    
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/agent/command/stream');
    
    ws.onopen = () => {
        // Send command as JSON
        ws.send(JSON.stringify({
            command: "your command here",
            user_id: "optional-user-id"
        }));
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'chunk') {
            // Handle streaming chunk
            console.log(data.content);
        } else if (data.type === 'done') {
            // Stream complete, connection stays open for more commands
            console.log('Command completed');
        } else if (data.type === 'error') {
            // Handle error
            console.error(data.error);
        }
    };
    
    // Connection will auto-close after 5 minutes of inactivity
    // Or close manually: ws.close();
    ```
    
    The server will send JSON messages with the following structure:
    - `{"type": "chunk", "content": "text chunk"}` - A piece of the response
    - `{"type": "done"}` - Indicates the stream is complete (connection stays open)
    - `{"type": "error", "error": "error message"}` - Indicates an error occurred
    """
    connection_id = await websocket_manager.accept_connection(websocket)
    
    try:
        # Keep connection alive and process multiple commands
        while True:
            # Wait for a command message
            data = await websocket_manager.receive_message(connection_id)
            if data is None:
                # Connection was closed
                break
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket_manager.send_message(connection_id, {
                    "type": "error",
                    "error": "Invalid JSON format. Expected: {\"command\": \"...\", \"user_id\": \"...\"}"
                })
                continue
            
            command = message.get("command", "")
            user_id = message.get("user_id")
            
            if not command:
                await websocket_manager.send_message(connection_id, {
                    "type": "error",
                    "error": "Command is required"
                })
                continue
            
            logger.info(f"Processing command via WebSocket [{connection_id}]: {command[:50]}...")
            
            # Create a CommandRequest-like object for the controller
            request = CommandRequest(command=command, user_id=user_id)
            
            # Stream chunks back to the client
            try:
                async for chunk in controller.process_command_stream(request):
                    # Send each chunk as a JSON message
                    sent = await websocket_manager.send_message(connection_id, {
                        "type": "chunk",
                        "content": chunk
                    })
                    if not sent:
                        # Connection was closed
                        break
                
                # Send completion message
                await websocket_manager.send_message(connection_id, {
                    "type": "done"
                })
                
            except Exception as e:
                logger.error(f"Error processing command stream [{connection_id}]: {e}")
                await websocket_manager.send_message(connection_id, {
                    "type": "error",
                    "error": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {connection_id}")
        await websocket_manager.close_connection(connection_id, reason="client_disconnect")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handler [{connection_id}]: {e}")
        await websocket_manager.close_connection(connection_id, reason="unexpected_error")
