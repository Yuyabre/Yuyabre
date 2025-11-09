"""
Controller for WhatsApp-related operations.
"""
from typing import Dict, Any, Optional
from loguru import logger

from modules.whatsapp import WhatsAppService
from modules.ordering import OrderingService
from api.dependencies import agent
from models.order import Order
from models.user import User


class WhatsAppController:
    """Controller for handling WhatsApp webhook messages."""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.ordering_service = OrderingService()
        self.agent = agent  # Use shared agent instance for conversation context
    
    async def process_incoming_message(
        self,
        from_number: str,
        message_body: str,
        message_sid: str,
    ) -> Dict[str, Any]:
        """
        Process an incoming WhatsApp message.
        
        Args:
            from_number: Phone number that sent the message (format: whatsapp:+1234567890)
            message_body: Message content
            message_sid: Twilio message SID
            
        Returns:
            Dict with success status and optional error message
        """
        try:
            # Extract phone number (remove whatsapp: prefix)
            phone_number = from_number.replace("whatsapp:", "")
            
            # Find user by phone number
            user = await User.find_one(User.phone == phone_number)
            if not user:
                logger.warning(f"No user found for phone number: {phone_number}")
                return {"success": False, "error": "User not found"}
            
            # Relay message to agent for context
            # Format: "WhatsApp message: {message_body}"
            whatsapp_context = f"WhatsApp message from {user.name}: {message_body}"
            await self.agent.add_message_to_conversation(
                user_id=user.user_id,
                message=whatsapp_context,
                role="user"
            )
            logger.info(f"Relayed WhatsApp message to agent for user {user.user_id}")
            
            # Check if this is a response to a pending group order
            # Look for pending group orders for this user's household
            if not user.household_id:
                return {"success": False, "error": "User not in a household"}
            
            # Find pending group orders
            from models.order import OrderStatus
            pending_orders = await Order.find(
                Order.household_id == user.household_id,
                Order.is_group_order == True,
                Order.status == OrderStatus.PENDING
            ).to_list()
            
            if not pending_orders:
                return {"success": True, "message": "No pending orders"}
            
            # Get the most recent pending order
            order = pending_orders[0]  # Could be improved to match by order ID in message
            
            # Check if user needs to respond to this order
            user_needs_to_respond = False
            for item_name, pending_users in order.pending_responses.items():
                if user.user_id in pending_users:
                    user_needs_to_respond = True
                    break
            
            if not user_needs_to_respond:
                return {"success": True, "message": "No response needed"}
            
            # Parse the response
            order_items = [
                {"name": item.name, "quantity": item.quantity, "unit": item.unit}
                for item in order.items
            ]
            
            parsed_response = self.whatsapp_service.parse_order_response(
                message_body,
                order_items
            )
            
            # Process the response
            updated_order = await self.ordering_service.process_group_order_response(
                order_id=order.order_id,
                user_id=user.user_id,
                responses=parsed_response,
            )
            
            if updated_order:
                # Send confirmation message
                if parsed_response.get("confirmed"):
                    items_str = ", ".join([
                        f"{item['name']} ({item.get('quantity', 1)})"
                        for item in parsed_response.get("items", [])
                    ])
                    confirmation = f"✅ Added to order: {items_str}"
                else:
                    confirmation = "✅ Noted - you don't need these items."
                
                # Send confirmation via WhatsApp
                if user.phone:
                    await self.whatsapp_service.send_message(
                        to=user.phone,
                        message=confirmation
                    )
                
                return {"success": True, "message": "Response processed"}
            else:
                return {"success": False, "error": "Failed to process response"}
                
        except Exception as e:
            logger.error(f"Error processing WhatsApp message: {e}")
            return {"success": False, "error": str(e)}

