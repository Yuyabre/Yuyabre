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
    Webhook endpoint for receiving Discord messages and reactions.
    
    This endpoint receives incoming Discord messages and reactions from the bot
    and processes responses to group orders.
    
    Supports two types of events:
    - "message": Regular Discord messages
    - "reaction": Discord message reactions (emoji)
    """
    try:
        # Get JSON data from Discord webhook
        data = await request.json()
        
        event_type = data.get("type", "message")  # Default to "message" for backward compatibility
        
        if event_type == "reaction":
            # Process reaction event
            user_id = data.get("user_id") or data.get("author", {}).get("id")
            channel_id = data.get("channel_id")
            message_id = data.get("message_id")
            emoji = data.get("emoji", "")
            emoji_name = data.get("emoji_name", "")
            action = data.get("action", "add")
            author_name = data.get("author", {}).get("username") or data.get("username", "Unknown")
            message_content = data.get("message_content", "")
            
            logger.info(
                f"Received Discord reaction from {author_name} in channel {channel_id}: "
                f"{emoji} ({action}) on message {message_id}"
            )
            
            # Process the reaction
            result = await controller.process_incoming_reaction(
                user_id=str(user_id) if user_id else "",
                channel_id=str(channel_id) if channel_id else "",
                message_id=str(message_id) if message_id else "",
                emoji=emoji,
                emoji_name=emoji_name,
                action=action,
                author_name=author_name,
                message_content=message_content,
            )
            
            # Return success response
            if result.get("success"):
                return {"status": "ok", "message": result.get("message", "Reaction processed")}
            else:
                return Response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": result.get("error", "Error processing reaction")}
                )
        else:
            # Process message event (default)
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
        import traceback
        logger.debug(traceback.format_exc())
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )

