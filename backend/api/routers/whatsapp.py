"""
Router for WhatsApp webhook endpoints.
"""
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import Response
from loguru import logger
from typing import Dict, Any

from api.controllers.whatsapp_controller import WhatsAppController

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

controller = WhatsAppController()


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Webhook endpoint for receiving WhatsApp messages from Twilio.
    
    This endpoint receives incoming WhatsApp messages and processes
    responses to group orders.
    """
    try:
        # Get form data from Twilio webhook
        form_data = await request.form()
        
        # Extract message details
        from_number = form_data.get("From", "")
        message_body = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid", "")
        
        logger.info(f"Received WhatsApp message from {from_number}: {message_body[:50]}")
        
        # Process the message
        result = await controller.process_incoming_message(
            from_number=from_number,
            message_body=message_body,
            message_sid=message_sid,
        )
        
        # Return TwiML response (Twilio expects XML)
        if result.get("success"):
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
                media_type="application/xml"
            )
        else:
            # Optionally send an error message back
            error_msg = result.get("error", "Error processing message")
            return Response(
                content=f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{error_msg}</Message></Response>',
                media_type="application/xml"
            )
            
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )

