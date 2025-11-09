"""
WhatsApp Service - Integration with Twilio WhatsApp API.

Handles sending messages to WhatsApp groups and receiving responses.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from beanie.operators import In

from config import settings
from models.household import Household
from models.user import User


class WhatsAppService:
    """
    Service for sending and receiving WhatsApp messages.
    
    Uses Twilio WhatsApp API for messaging functionality.
    Note: Twilio doesn't directly support WhatsApp groups, so we send
    messages to individual numbers and aggregate responses.
    """
    
    def __init__(self):
        """Initialize WhatsApp service with Twilio client."""
        self.account_sid = settings.whatsapp_account_sid
        self.auth_token = settings.whatsapp_auth_token
        self.from_number = settings.whatsapp_from_number
        self.client = None
        
        if self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("WhatsApp service initialized with Twilio")
            except ImportError:
                logger.warning("Twilio library not installed. Install with: pip install twilio")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
        else:
            logger.warning("WhatsApp credentials not configured")
    
    def is_configured(self) -> bool:
        """Check if WhatsApp service is properly configured."""
        return (
            self.client is not None
            and self.account_sid is not None
            and self.auth_token is not None
            and self.from_number is not None
        )
    
    async def send_message(
        self,
        to: str,
        message: str,
    ) -> Optional[str]:
        """
        Send a WhatsApp message to a phone number.
        
        Args:
            to: Phone number in international format (e.g., "+31612345678")
            message: Message content to send
            
        Returns:
            Message SID if successful, None otherwise
        """
        if not self.is_configured():
            logger.warning("WhatsApp service not configured, cannot send message")
            return None
        
        try:
            # Format phone number for WhatsApp
            if not to.startswith("whatsapp:"):
                to = f"whatsapp:{to}"
            
            # Send message via Twilio
            twilio_message = self.client.messages.create(
                from_=self.from_number,
                body=message,
                to=to
            )
            
            logger.info(f"WhatsApp message sent to {to}: {twilio_message.sid}")
            return twilio_message.sid
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {to}: {e}")
            return None
    
    async def send_to_household(
        self,
        household_id: str,
        message: str,
    ) -> Dict[str, Optional[str]]:
        """
        Send a WhatsApp message to all members of a household.
        
        Args:
            household_id: ID of the household
            message: Message content to send
            
        Returns:
            Dict mapping user_id to message SID (or None if failed)
        """
        if not self.is_configured():
            logger.warning("WhatsApp service not configured")
            return {}
        
        # Get household
        household = await Household.find_one(Household.household_id == household_id)
        if not household:
            logger.error(f"Household not found: {household_id}")
            return {}
        
        # Get all household members
        if not household.member_ids:
            logger.warning(f"Household {household_id} has no members")
            return {}
        
        users = await User.find(
            In(User.user_id, household.member_ids),
            User.is_active == True
        ).to_list()
        
        results = {}
        for user in users:
            if user.phone:
                message_sid = await self.send_message(user.phone, message)
                results[user.user_id] = message_sid
            else:
                logger.warning(f"User {user.user_id} has no phone number")
                results[user.user_id] = None
        
        return results
    
    async def send_group_order_notification(
        self,
        household_id: str,
        order_id: str,
        items: List[Dict[str, Any]],
        created_by_user: str,
        response_deadline: datetime,
        notify_user_ids: Optional[List[str]] = None,
    ) -> bool:
        """
        Send a group order notification to household members.
        
        Args:
            household_id: ID of the household
            order_id: Order ID
            items: List of items in the order (with name, quantity, unit)
            created_by_user: User ID who created the order
            response_deadline: Deadline for responses
            notify_user_ids: Optional list of user IDs to notify. If None, notifies all household members.
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        # Get creator's name
        creator = await User.find_one(User.user_id == created_by_user)
        creator_name = creator.name if creator else "Someone"
        
        # Format deadline
        deadline_str = response_deadline.strftime("%Y-%m-%d %H:%M")
        
        # Build message
        message_lines = [
            f"🛒 *New Group Order*",
            f"",
            f"Created by: {creator_name}",
            f"",
            f"*Items:*"
        ]
        
        for item in items:
            item_name = item.get("name", "Unknown")
            quantity = item.get("quantity", 0)
            unit = item.get("unit", "")
            message_lines.append(f"• {item_name}: {quantity} {unit}")
        
        message_lines.extend([
            f"",
            f"Please reply with which items you also need.",
            f"Format: *YES* for items you want, or specify quantities.",
            f"",
            f"Deadline: {deadline_str}",
            f"",
            f"Order ID: {order_id}"
        ])
        
        message = "\n".join(message_lines)
        
        # Send to specified users or all household members
        if notify_user_ids:
            # Send to specific users only
            results = {}
            for user_id in notify_user_ids:
                user = await User.find_one(User.user_id == user_id)
                if user and user.phone:
                    message_sid = await self.send_message(user.phone, message)
                    results[user_id] = message_sid
                else:
                    logger.warning(f"User {user_id} not found or has no phone number")
                    results[user_id] = None
        else:
            # Send to all household members (default behavior)
            results = await self.send_to_household(household_id, message)
        
        # Check if at least one message was sent
        success = any(sid is not None for sid in results.values())
        
        if success:
            logger.info(f"Group order notification sent for order {order_id}")
        else:
            logger.error(f"Failed to send group order notification for order {order_id}")
        
        return success
    
    async def send_order_update(
        self,
        household_id: str,
        order_id: str,
        update_message: str,
    ) -> bool:
        """
        Send an order update to household members.
        
        Args:
            household_id: ID of the household
            order_id: Order ID
            update_message: Update message to send
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        message = f"📦 *Order Update*\n\nOrder ID: {order_id}\n\n{update_message}"
        
        results = await self.send_to_household(household_id, message)
        success = any(sid is not None for sid in results.values())
        
        if success:
            logger.info(f"Order update sent for order {order_id}")
        else:
            logger.error(f"Failed to send order update for order {order_id}")
        
        return success
    
    def parse_order_response(
        self,
        message: str,
        order_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Parse a user's response to a group order notification.
        
        Args:
            message: User's response message
            order_items: List of items in the order
            
        Returns:
            Dict with parsed response:
            {
                "items": [{"name": "item_name", "quantity": 1.0}],
                "confirmed": True/False
            }
        """
        message_lower = message.lower().strip()
        
        # Check for explicit confirmations
        if any(word in message_lower for word in ["yes", "confirm", "add me", "i need"]):
            # User wants all items
            return {
                "items": [
                    {"name": item.get("name"), "quantity": item.get("quantity", 1.0)}
                    for item in order_items
                ],
                "confirmed": True
            }
        
        # Check for explicit rejections
        if any(word in message_lower for word in ["no", "skip", "pass", "not needed"]):
            return {
                "items": [],
                "confirmed": False
            }
        
        # Try to parse specific items and quantities
        # Simple parsing: look for item names and numbers
        parsed_items = []
        for item in order_items:
            item_name_lower = item.get("name", "").lower()
            if item_name_lower in message_lower:
                # Try to extract quantity
                import re
                # Look for numbers near the item name
                pattern = rf"{re.escape(item_name_lower)}.*?(\d+\.?\d*)"
                match = re.search(pattern, message_lower)
                if match:
                    quantity = float(match.group(1))
                else:
                    quantity = item.get("quantity", 1.0)
                
                parsed_items.append({
                    "name": item.get("name"),
                    "quantity": quantity
                })
        
        return {
            "items": parsed_items,
            "confirmed": len(parsed_items) > 0
        }

