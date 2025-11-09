"""
Discord Service - Integration with Discord Bot API.

Handles sending messages to Discord channels and receiving responses.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from beanie.operators import In

from config import settings
from models.household import Household
from models.user import User


class DiscordService:
    """
    Service for sending and receiving Discord messages.
    
    Uses discord.py library for Discord bot functionality.
    """
    
    def __init__(self):
        """Initialize Discord service with bot client."""
        self.bot_token = settings.discord_bot_token
        self.client = None
        self._bot_instance = None
        
        logger.info(f"Initializing Discord service. Bot token configured: {bool(self.bot_token)}")
        
        if self.bot_token:
            try:
                import discord
                from discord.ext import commands
                
                logger.debug("discord.py library imported successfully")
                
                # Set up intents
                intents = discord.Intents.default()
                intents.message_content = True
                intents.messages = True
                
                logger.debug("Discord intents configured: message_content=True, messages=True")
                
                # Create bot instance
                self._bot_instance = commands.Bot(
                    command_prefix='!',
                    intents=intents
                )
                
                logger.debug("Discord bot instance created")
                
                # Set up event handlers
                self._setup_event_handlers()
                
                logger.info("Discord service initialized successfully. Bot instance ready for connection.")
            except ImportError as e:
                logger.error(f"discord.py library not installed. Install with: pip install discord.py. Error: {e}")
            except Exception as e:
                logger.error(f"Failed to initialize Discord client: {e}", exc_info=True)
        else:
            logger.warning("Discord bot token not configured. Set DISCORD_BOT_TOKEN environment variable.")
    
    def _setup_event_handlers(self):
        """Set up Discord bot event handlers."""
        if not self._bot_instance:
            return
        
        @self._bot_instance.event
        async def on_ready():
            bot_user = self._bot_instance.user
            guild_count = len(self._bot_instance.guilds)
            logger.info(f'Discord bot logged in as {bot_user} (ID: {bot_user.id if bot_user else "unknown"})')
            logger.info(f'Discord bot is ready and connected to {guild_count} server(s)')
            logger.debug(f'Discord bot ready state: is_ready()={self._bot_instance.is_ready()}')
        
        @self._bot_instance.event
        async def on_interaction(interaction):
            """Handle all interactions (button clicks, etc.)"""
            if interaction.type.name == "component":
                # This is a button click or other component interaction
                # The callback is already set in the button, so it will be called automatically
                # But we need to make sure the bot processes it
                pass
        
        @self._bot_instance.event
        async def on_message(message):
            # Ignore messages from the bot itself
            if message.author == self._bot_instance.user:
                return
            
            # Forward message to webhook endpoint
            await self._forward_message_to_webhook(message)
            
            # Process commands
            await self._bot_instance.process_commands(message)
    
    async def _forward_message_to_webhook(self, message):
        """Forward incoming Discord message to webhook endpoint."""
        try:
            import httpx
            
            webhook_url = f"http://localhost:8000/discord/webhook"
            
            payload = {
                "user_id": str(message.author.id),
                "channel_id": str(message.channel.id),
                "content": message.content,
                "author": {
                    "id": str(message.author.id),
                    "username": message.author.name,
                },
                "username": message.author.name,
            }
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(webhook_url, json=payload)
                if response.status_code == 200:
                    logger.debug(f"Forwarded Discord message to webhook: {message.id}")
                else:
                    logger.warning(f"Failed to forward Discord message to webhook: {response.status_code}")
        except Exception as e:
            logger.error(f"Error forwarding Discord message to webhook: {e}")
    
    def is_configured(self) -> bool:
        """Check if Discord service is properly configured."""
        configured = (
            self._bot_instance is not None
            and self.bot_token is not None
        )
        logger.debug(f"Discord service configured check: {configured} (bot_instance={self._bot_instance is not None}, token={bool(self.bot_token)})")
        return configured
    
    async def start_bot(self):
        """Start the Discord bot (should be run in a background task)."""
        logger.info("Attempting to start Discord bot...")
        
        if not self.is_configured():
            logger.error("Discord service not configured, cannot start bot")
            return
        
        if not self._bot_instance:
            logger.error("Discord bot instance is None, cannot start")
            return
        
        logger.info(f"Starting Discord bot with token (first 10 chars): {self.bot_token[:10]}...")
        logger.debug(f"Bot instance exists: {self._bot_instance is not None}")
        logger.debug(f"Bot ready state before start: {self._bot_instance.is_ready()}")
        
        try:
            import discord
            logger.info("Calling bot.start() - this will block until bot connects...")
            await self._bot_instance.start(self.bot_token)
            logger.info("Discord bot.start() completed (this should not happen unless bot disconnects)")
        except Exception as e:
            # Check if it's a discord-specific error
            error_type = type(e).__name__
            if "LoginFailure" in error_type or "login" in str(e).lower():
                logger.error(f"Discord bot login failed - invalid token: {e}")
            elif "PrivilegedIntentsRequired" in error_type or "privileged" in str(e).lower():
                logger.error(f"Discord bot requires privileged intents: {e}")
            else:
                logger.error(f"Failed to start Discord bot: {e}", exc_info=True)
    
    async def stop_bot(self):
        """Stop the Discord bot."""
        if self._bot_instance:
            await self._bot_instance.close()
    
    async def send_message_to_channel(
        self,
        channel_id: int,
        message: str,
    ) -> Optional[int]:
        """
        Send a message to a Discord channel.
        
        Args:
            channel_id: Discord channel ID (integer)
            message: Message content to send
            
        Returns:
            Message ID if successful, None otherwise
        """
        logger.info(f"Attempting to send Discord message to channel {channel_id}")
        logger.debug(f"Message content (first 50 chars): {message[:50]}...")
        
        if not self.is_configured():
            logger.error("Discord service not configured, cannot send message")
            return None
        
        if not self._bot_instance:
            logger.error("Discord bot instance is None, cannot send message")
            return None
        
        try:
            import discord
            
            # Check bot ready state
            is_ready = self._bot_instance.is_ready()
            logger.debug(f"Discord bot ready state: {is_ready}")
            logger.debug(f"Discord bot user: {self._bot_instance.user}")
            logger.debug(f"Discord bot connected: {self._bot_instance.is_ws_ratelimited if hasattr(self._bot_instance, 'is_ws_ratelimited') else 'unknown'}")
            
            # Wait for bot to be ready if it's not yet
            if not is_ready:
                logger.warning(f"Discord bot not ready yet. Current state: is_ready()={is_ready}, user={self._bot_instance.user}")
                logger.info("Waiting for Discord bot to become ready (max 5 seconds)...")
                # Wait up to 5 seconds for bot to be ready
                import asyncio
                for i in range(10):
                    await asyncio.sleep(0.5)
                    is_ready_now = self._bot_instance.is_ready()
                    logger.debug(f"Wait attempt {i+1}/10: bot ready={is_ready_now}")
                    if is_ready_now:
                        logger.info("Discord bot became ready!")
                        break
                else:
                    logger.error(f"Discord bot did not become ready in time (waited 5 seconds)")
                    logger.error(f"Final state: is_ready()={self._bot_instance.is_ready()}, user={self._bot_instance.user}")
                    logger.error("Possible causes: bot not started, connection failed, or invalid token")
                    return None
            
            # Get channel - try both get_channel and fetch_channel
            logger.debug(f"Attempting to get Discord channel {channel_id}")
            channel = self._bot_instance.get_channel(channel_id)
            logger.debug(f"get_channel() result: {channel} (type: {type(channel).__name__ if channel else None})")
            
            if not channel:
                # Try fetching the channel
                logger.debug(f"Channel not found in cache, attempting fetch_channel()...")
                try:
                    channel = await self._bot_instance.fetch_channel(channel_id)
                    logger.debug(f"fetch_channel() successful: {channel} (type: {type(channel).__name__})")
                except discord.errors.Forbidden as fetch_error:
                    logger.error(f"Discord bot lacks permission to access channel {channel_id}: {fetch_error}")
                    return None
                except discord.errors.NotFound as fetch_error:
                    logger.error(f"Discord channel {channel_id} not found: {fetch_error}")
                    return None
                except Exception as fetch_error:
                    logger.error(f"Error fetching Discord channel {channel_id}: {fetch_error}", exc_info=True)
                    return None
            
            if not channel:
                logger.error(f"Discord channel {channel_id} not found or not accessible after all attempts")
                return None
            
            logger.info(f"Sending message to Discord channel {channel_id} ({channel.name if hasattr(channel, 'name') else 'unknown'})")
            try:
                sent_message = await channel.send(message)
                logger.info(f"Discord message sent successfully to channel {channel_id}: message ID {sent_message.id}")
                return sent_message.id
            except discord.errors.Forbidden as send_error:
                logger.error(f"Discord bot lacks permission to send messages to channel {channel_id}: {send_error}")
                logger.error("Check bot permissions: Send Messages, View Channels")
                return None
            except Exception as send_error:
                logger.error(f"Error sending message to Discord channel {channel_id}: {send_error}", exc_info=True)
                return None
            
        except discord.errors.Forbidden as e:
            logger.error(f"Discord bot lacks permission to send messages to channel {channel_id}: {e}")
            logger.error("Required permissions: Send Messages, View Channels, Read Message History")
            return None
        except discord.errors.NotFound as e:
            logger.error(f"Discord channel {channel_id} not found: {e}")
            logger.error("Verify the channel ID is correct and the bot has access to the channel")
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending Discord message to channel {channel_id}: {e}", exc_info=True)
            return None
    
    async def send_to_household(
        self,
        household_id: str,
        message: str,
    ) -> Dict[str, Optional[int]]:
        """
        Send a Discord message to the household's Discord channel.
        
        Args:
            household_id: ID of the household
            message: Message content to send
            
        Returns:
            Dict mapping user_id to message ID (or None if failed)
        """
        if not self.is_configured():
            logger.warning("Discord service not configured")
            return {}
        
        # Get household
        household = await Household.find_one(Household.household_id == household_id)
        if not household:
            logger.error(f"Household not found: {household_id}")
            return {}
        
        if not household.discord_channel_id:
            logger.warning(f"Household {household_id} has no Discord channel configured")
            return {}
        
        # Send message to Discord channel
        message_id = await self.send_message_to_channel(
            int(household.discord_channel_id),
            message
        )
        
        # Return results for all household members
        results = {}
        if household.member_ids:
            for member_id in household.member_ids:
                results[member_id] = message_id
        else:
            results["household"] = message_id
        
        return results
    
    async def send_group_order_notification(
        self,
        household_id: str,
        order_id: str,
        items: List[Dict[str, Any]],
        created_by_user: str,
        response_deadline: datetime,
    ) -> bool:
        """
        Send a group order notification to household members via Discord with YES/NO buttons.
        
        Args:
            household_id: ID of the household
            order_id: Order ID
            items: List of items in the order (with name, quantity, unit)
            created_by_user: User ID who created the order
            response_deadline: Deadline for responses
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("Discord service not configured, cannot send group order notification")
            return False
        
        try:
            import discord
            
            # Get household
            household = await Household.find_one(Household.household_id == household_id)
            if not household or not household.discord_channel_id:
                logger.error(f"Household {household_id} not found or has no Discord channel")
                return False
            
            # Get creator's name
            creator = await User.find_one(User.user_id == created_by_user)
            creator_name = creator.name if creator else "Someone"
            
            # Format deadline
            deadline_str = response_deadline.strftime("%Y-%m-%d %H:%M")
            
            # Build message with Discord formatting
            message_lines = [
                f"🛒 **New Group Order**",
                f"",
                f"Created by: **{creator_name}**",
                f"",
                f"**Items:**"
            ]
            
            for item in items:
                item_name = item.get("name", "Unknown")
                quantity = item.get("quantity", 0)
                unit = item.get("unit", "")
                message_lines.append(f"• {item_name}: {quantity} {unit}")
            
            message_lines.extend([
                f"",
                f"**Do you need these items?** Click a button below to respond.",
                f"",
                f"⏰ Deadline: {deadline_str}",
                f"",
                f"Order ID: `{order_id}`"
            ])
            
            message_content = "\n".join(message_lines)
            
            # Create Discord View with buttons
            view = discord.ui.View(timeout=None)  # No timeout - buttons stay active
            
            # YES button - user wants the items
            yes_button = discord.ui.Button(
                label="✅ YES, I need these",
                style=discord.ButtonStyle.success,
                custom_id=f"order_{order_id}_yes"
            )
            
            # NO button - user doesn't need the items
            no_button = discord.ui.Button(
                label="❌ NO, I don't need these",
                style=discord.ButtonStyle.danger,
                custom_id=f"order_{order_id}_no"
            )
            
            # Add button callbacks
            async def yes_callback(interaction: discord.Interaction):
                await self._handle_order_button_response(
                    interaction=interaction,
                    order_id=order_id,
                    response="yes"
                )
            
            async def no_callback(interaction: discord.Interaction):
                await self._handle_order_button_response(
                    interaction=interaction,
                    order_id=order_id,
                    response="no"
                )
            
            yes_button.callback = yes_callback
            no_button.callback = no_callback
            
            view.add_item(yes_button)
            view.add_item(no_button)
            
            # Wait for bot to be ready
            if not self._bot_instance.is_ready():
                import asyncio
                for _ in range(10):
                    await asyncio.sleep(0.5)
                    if self._bot_instance.is_ready():
                        break
                else:
                    logger.error("Discord bot did not become ready in time")
                    return False
            
            # Get channel and send message with buttons
            channel = self._bot_instance.get_channel(int(household.discord_channel_id))
            if not channel:
                try:
                    channel = await self._bot_instance.fetch_channel(int(household.discord_channel_id))
                except Exception as e:
                    logger.error(f"Discord channel {household.discord_channel_id} not found: {e}")
                    return False
            
            sent_message = await channel.send(content=message_content, view=view)
            logger.info(f"Discord group order notification sent with buttons for order {order_id}: message {sent_message.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Discord group order notification: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    async def _handle_order_button_response(
        self,
        interaction,
        order_id: str,
        response: str,
    ):
        """
        Handle button click response for group order.
        
        Args:
            interaction: Discord interaction object
            order_id: Order ID
            response: "yes" or "no"
        """
        try:
            import discord
            
            # Acknowledge the interaction immediately
            await interaction.response.defer(ephemeral=True)
            
            # Get user info
            discord_user_id = str(interaction.user.id)
            channel_id = str(interaction.channel.id)
            user_name = interaction.user.name
            
            logger.info(f"Discord button clicked: order={order_id}, response={response}, user={user_name} ({discord_user_id})")
            
            # Find user by Discord ID
            user = await User.find_one(User.discord_user_id == discord_user_id)
            
            if not user:
                # Try to find by channel and name
                from models.household import Household
                household = await Household.find_one(Household.discord_channel_id == channel_id)
                if household:
                    users = await User.find(
                        User.household_id == household.household_id,
                        User.is_active == True
                    ).to_list()
                    for u in users:
                        if u.name.lower() == user_name.lower():
                            user = u
                            if not u.discord_user_id:
                                u.discord_user_id = discord_user_id
                                await u.save()
                            break
            
            if not user:
                await interaction.followup.send(
                    "❌ User not found. Please ensure your Discord user ID is set in your profile.",
                    ephemeral=True
                )
                return
            
            # Find the order
            from models.order import Order, OrderStatus
            order = await Order.find_one(Order.order_id == order_id)
            
            if not order:
                await interaction.followup.send(
                    f"❌ Order {order_id} not found.",
                    ephemeral=True
                )
                return
            
            # Check if user needs to respond
            user_needs_to_respond = False
            pending_item_names = []
            for item_name, pending_users in order.pending_responses.items():
                if user.user_id in pending_users:
                    user_needs_to_respond = True
                    pending_item_names.append(item_name)
            
            if not user_needs_to_respond:
                await interaction.followup.send(
                    "✅ You've already responded to this order.",
                    ephemeral=True
                )
                return
            
            # Prepare response based on button clicked
            if response == "yes":
                # User wants the items - use default quantities from order
                parsed_response = {
                    "confirmed": True,
                    "items": [
                        {
                            "name": item.name,
                            "quantity": item.quantity,
                            "unit": item.unit
                        }
                        for item in order.items
                        if item.name in pending_item_names
                    ]
                }
                confirmation_msg = f"✅ Added to order: {', '.join(pending_item_names)}"
            else:  # "no"
                # User doesn't need the items
                parsed_response = {
                    "confirmed": False,
                    "items": []
                }
                confirmation_msg = "✅ Noted - you don't need these items."
            
            # Process the response via ordering service
            from modules.ordering import OrderingService
            ordering_service = OrderingService()
            updated_order = await ordering_service.process_group_order_response(
                order_id=order_id,
                user_id=user.user_id,
                responses=parsed_response,
            )
            
            if updated_order:
                # Send public confirmation in channel
                from models.household import Household
                household = await Household.find_one(Household.household_id == user.household_id)
                if household and household.discord_channel_id:
                    channel = self._bot_instance.get_channel(int(household.discord_channel_id))
                    if channel:
                        await channel.send(f"**{user.name}**: {confirmation_msg}")
                
                # Relay response back to agent
                from api.dependencies import agent
                agent_context = f"Discord response from {user.name} for order {order_id}: {confirmation_msg}"
                await agent.add_message_to_conversation(
                    user_id=user.user_id,
                    message=agent_context,
                    role="user"
                )
                
                # Send ephemeral confirmation to user
                await interaction.followup.send(
                    confirmation_msg,
                    ephemeral=True
                )
                
                logger.info(f"Processed Discord button response for order {order_id} from user {user.user_id}: {response}")
            else:
                await interaction.followup.send(
                    "❌ Failed to process your response. Please try again.",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error handling Discord button response: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            try:
                await interaction.followup.send(
                    "❌ An error occurred processing your response.",
                    ephemeral=True
                )
            except:
                pass
    
    async def send_order_update(
        self,
        household_id: str,
        order_id: str,
        update_message: str,
    ) -> bool:
        """
        Send an order update to household members via Discord.
        
        Args:
            household_id: ID of the household
            order_id: Order ID
            update_message: Update message to send
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        message = f"📦 **Order Update**\n\nOrder ID: `{order_id}`\n\n{update_message}"
        
        results = await self.send_to_household(household_id, message)
        success = any(mid is not None for mid in results.values())
        
        if success:
            logger.info(f"Discord order update sent for order {order_id}")
        else:
            logger.error(f"Failed to send Discord order update for order {order_id}")
        
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
    
    def get_message_handler(self):
        """Get the bot instance for setting up message handlers."""
        return self._bot_instance

