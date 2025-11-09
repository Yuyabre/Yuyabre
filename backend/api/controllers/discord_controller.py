"""
Controller for Discord-related operations.
"""
from typing import Dict, Any, Optional
from loguru import logger

from modules.discord import DiscordService
from modules.ordering import OrderingService
from api.dependencies import agent
from models.order import Order
from models.user import User


class DiscordController:
    """Controller for handling Discord bot messages."""
    
    def __init__(self):
        self.discord_service = DiscordService()
        self.ordering_service = OrderingService()
        self.agent = agent  # Use shared agent instance for conversation context
    
    async def process_incoming_message(
        self,
        user_id: str,
        channel_id: str,
        message_content: str,
        author_name: str,
    ) -> Dict[str, Any]:
        """
        Process an incoming Discord message.
        
        Args:
            user_id: Discord user ID (we'll need to map this to our User model)
            channel_id: Discord channel ID where message was sent
            message_content: Message content
            author_name: Discord username
            
        Returns:
            Dict with success status and optional error message
        """
        try:
            # Find household by channel_id first
            from models.household import Household
            household = await Household.find_one(Household.discord_channel_id == channel_id)
            
            if not household:
                logger.warning(f"No household found for Discord channel: {channel_id}")
                return {"success": False, "error": "Channel not linked to household"}
            
            # Try to find user by Discord user ID first (most reliable)
            user = None
            if user_id:
                user = await User.find_one(User.discord_user_id == str(user_id))
            
            # Fallback: Try to find user by name in household members
            if not user:
                users = await User.find(
                    User.household_id == household.household_id,
                    User.is_active == True
                ).to_list()
                
                # Try to match by name (case-insensitive)
                for u in users:
                    if u.name.lower() == author_name.lower():
                        user = u
                        # Update user with Discord ID if we found them by name
                        if not u.discord_user_id and user_id:
                            u.discord_user_id = str(user_id)
                            await u.save()
                            logger.info(f"Updated user {u.user_id} with Discord user ID: {user_id}")
                        break
            
            if not user:
                logger.warning(f"No user found for Discord message from {author_name} (ID: {user_id}) in channel {channel_id}")
                return {"success": False, "error": "User not found. Please ensure your Discord user ID is set in your profile."}
            
            # Relay message to agent for context
            discord_context = f"Discord message from {user.name}: {message_content}"
            await self.agent.add_message_to_conversation(
                user_id=user.user_id,
                message=discord_context,
                role="user"
            )
            logger.info(f"Relayed Discord message to agent for user {user.user_id}")
            
            # Check if this is a response to a pending group order
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
            order = pending_orders[0]
            
            # Check if user needs to respond to this order
            user_needs_to_respond = False
            for item_name, pending_users in order.pending_responses.items():
                if user.user_id in pending_users:
                    user_needs_to_respond = True
                    break
            
            if not user_needs_to_respond:
                return {"success": True, "message": "No response needed"}
            
            # Parse the response - only use items that are in pending_responses for this user
            pending_item_names = [
                item_name for item_name, pending_users in order.pending_responses.items()
                if user.user_id in pending_users
            ]
            
            # Get only the items that are pending for this user
            order_items = [
                {"name": item.name, "quantity": item.quantity, "unit": item.unit}
                for item in order.items
                if item.name in pending_item_names
            ]
            
            logger.info(f"Processing Discord response for order {order.order_id}. Pending items for user: {pending_item_names}")
            
            parsed_response = self.discord_service.parse_order_response(
                message_content,
                order_items
            )
            
            logger.info(f"Parsed Discord response: {parsed_response}")
            
            # Process the response
            updated_order = await self.ordering_service.process_group_order_response(
                order_id=order.order_id,
                user_id=user.user_id,
                responses=parsed_response,
            )
            
            if updated_order:
                # Send confirmation message via Discord
                if parsed_response.get("confirmed") and parsed_response.get("items"):
                    items_str = ", ".join([
                        f"{item['name']} ({item.get('quantity', 1)})"
                        for item in parsed_response.get("items", [])
                    ])
                    confirmation = f"✅ Added to order: {items_str}"
                elif parsed_response.get("confirmed"):
                    items_str = ", ".join(pending_item_names)
                    confirmation = f"✅ Added to order: {items_str}"
                else:
                    confirmation = "✅ Noted - you don't need these items."
                
                # Send confirmation via Discord
                if household.discord_channel_id:
                    await self.discord_service.send_message_to_channel(
                        int(household.discord_channel_id),
                        f"{user.name}: {confirmation}"
                    )
                
                # Also relay the confirmation back to agent so it appears in CLI
                confirmation_context = f"Discord confirmation sent: {confirmation}"
                await self.agent.add_message_to_conversation(
                    user_id=user.user_id,
                    message=confirmation_context,
                    role="assistant"
                )
                
                return {"success": True, "message": "Response processed"}
            else:
                return {"success": False, "error": "Failed to process response"}
                
        except Exception as e:
            logger.error(f"Error processing Discord message: {e}")
            return {"success": False, "error": str(e)}

