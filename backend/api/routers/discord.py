"""
Router for Discord webhook endpoints.
"""
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import Response
from loguru import logger
from typing import Dict, Any

from api.controllers.discord_controller import DiscordController

router = APIRouter(prefix="/discord", tags=["Discord"])

controller = DiscordController()


@router.post("/webhook")
async def discord_webhook(request: Request):
    """
    Webhook endpoint for receiving Discord messages.
    
    This endpoint receives incoming Discord messages from the bot
    and processes responses to group orders.
    """
    try:
        # Get JSON data from Discord webhook
        data = await request.json()
        
        # Extract message details (Discord webhook format)
        # Adjust based on your Discord webhook setup
        user_id = data.get("user_id") or data.get("author", {}).get("id")
        channel_id = data.get("channel_id")
        message_content = data.get("content") or data.get("message", "")
        author_name = data.get("author", {}).get("username") or data.get("username", "Unknown")
        
        logger.info(f"Received Discord message from {author_name} in channel {channel_id}: {message_content[:50]}")
        
        # Process the message
        result = await controller.process_incoming_message(
            user_id=str(user_id) if user_id else "",
            channel_id=str(channel_id) if channel_id else "",
            message_content=message_content,
            author_name=author_name,
        )
        
        # Return success response
        if result.get("success"):
            return {"status": "ok", "message": result.get("message", "Message processed")}
        else:
            return Response(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": result.get("error", "Error processing message")}
            )
            
    except Exception as e:
        logger.error(f"Error processing Discord webhook: {e}")
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )

