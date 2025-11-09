"""
Discord Service - Integration with Discord Bot API.

Handles sending messages to Discord channels and receiving responses.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid
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
        logger.info("=" * 60)
        logger.info("Discord Service: Initializing...")
        logger.info("=" * 60)

        self.bot_token = settings.discord_bot_token
        self.client = None
        self._bot_instance = None
        self._message_contexts: Dict[str, Dict[str, Any]] = {}

        token_configured = bool(self.bot_token)
        token_preview = (
            f"{self.bot_token[:10]}..."
            if self.bot_token and len(self.bot_token) > 10
            else "None"
        )

        logger.info(
            f"Discord bot token configured: {token_configured} (preview: {token_preview})"
        )

        if self.bot_token:
            try:
                import discord
                from discord.ext import commands

                logger.debug("✓ discord.py library imported successfully")

                # Set up intents
                intents = discord.Intents.default()
                intents.message_content = True
                intents.messages = True

                logger.debug(
                    f"Discord intents configured: message_content={intents.message_content}, messages={intents.messages}"
                )

                # Create bot instance
                self._bot_instance = commands.Bot(command_prefix="!", intents=intents)

                logger.debug("✓ Discord bot instance created successfully")

                # Set up event handlers
                self._setup_event_handlers()

                logger.info(
                    "✓ Discord service initialized successfully. Bot instance ready for connection."
                )
                logger.info("=" * 60)
            except ImportError as e:
                logger.error("=" * 60)
                logger.error(
                    "✗ DISCORD INITIALIZATION FAILED: discord.py library not installed"
                )
                logger.error(f"   Error: {e}")
                logger.error("   Solution: Install with: pip install discord.py")
                logger.error("=" * 60)
            except Exception as e:
                logger.error("=" * 60)
                logger.error("✗ DISCORD INITIALIZATION FAILED: Unexpected error")
                logger.error(f"   Error type: {type(e).__name__}")
                logger.error(f"   Error message: {e}")
                logger.error("=" * 60, exc_info=True)
        else:
            logger.warning("=" * 60)
            logger.warning("⚠ Discord bot token not configured")
            logger.warning(
                "   Set DISCORD_BOT_TOKEN environment variable to enable Discord integration"
            )
            logger.warning("=" * 60)

    def _setup_event_handlers(self):
        """Set up Discord bot event handlers."""
        if not self._bot_instance:
            return

        @self._bot_instance.event
        async def on_ready():
            bot_user = self._bot_instance.user
            guild_count = len(self._bot_instance.guilds)

            logger.info("=" * 60)
            logger.info("✓ DISCORD BOT READY")
            logger.info(
                f"   Bot User: {bot_user} (ID: {bot_user.id if bot_user else 'unknown'})"
            )
            logger.info(f"   Connected to {guild_count} server(s)")
            logger.info(f"   Ready state: {self._bot_instance.is_ready()}")

            # Log guild details
            if guild_count > 0:
                logger.info("   Servers:")
                for guild in self._bot_instance.guilds:
                    logger.info(f"     - {guild.name} (ID: {guild.id})")
            else:
                logger.warning(
                    "   ⚠ Bot is not in any servers. Invite the bot to your server."
                )

            logger.info("=" * 60)

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
                logger.debug(
                    f"Discord: Ignoring message from bot itself (message ID: {message.id})"
                )
                return

            logger.info(
                f"Discord: Received message from {message.author.name} in channel {message.channel.id}"
            )
            logger.debug(f"   Message ID: {message.id}")
            logger.debug(
                f"   Channel: {message.channel.name if hasattr(message.channel, 'name') else 'unknown'}"
            )
            logger.debug(
                f"   Content preview: {message.content[:100] if message.content else '(empty)'}"
            )

            # Forward message to webhook endpoint
            try:
                await self._forward_message_to_webhook(message)
            except Exception as e:
                logger.error(
                    f"Discord: Failed to forward message to webhook: {e}", exc_info=True
                )

            # Process commands
            try:
                await self._bot_instance.process_commands(message)
            except Exception as e:
                logger.error(f"Discord: Error processing commands: {e}", exc_info=True)

        @self._bot_instance.event
        async def on_reaction_add(reaction, user):
            """Handle reaction additions to messages."""
            # Ignore reactions from the bot itself
            if user == self._bot_instance.user:
                logger.debug(
                    f"Discord: Ignoring reaction from bot itself (emoji: {reaction.emoji})"
                )
                return

            logger.info(
                f"Discord: Reaction added by {user.name} - {reaction.emoji} on message {reaction.message.id}"
            )
            logger.debug(
                f"   User ID: {user.id}, Channel ID: {reaction.message.channel.id}"
            )

            # Forward reaction to webhook endpoint
            try:
                await self._forward_reaction_to_webhook(reaction, user, action="add")
            except Exception as e:
                logger.error(
                    f"Discord: Failed to forward reaction to webhook: {e}",
                    exc_info=True,
                )

        @self._bot_instance.event
        async def on_reaction_remove(reaction, user):
            """Handle reaction removals from messages."""
            # Ignore reactions from the bot itself
            if user == self._bot_instance.user:
                logger.debug(
                    f"Discord: Ignoring reaction removal from bot itself (emoji: {reaction.emoji})"
                )
                return

            logger.info(
                f"Discord: Reaction removed by {user.name} - {reaction.emoji} on message {reaction.message.id}"
            )
            logger.debug(
                f"   User ID: {user.id}, Channel ID: {reaction.message.channel.id}"
            )

            # Forward reaction to webhook endpoint
            try:
                await self._forward_reaction_to_webhook(reaction, user, action="remove")
            except Exception as e:
                logger.error(
                    f"Discord: Failed to forward reaction removal to webhook: {e}",
                    exc_info=True,
                )

    async def _forward_message_to_webhook(self, message):
        """Forward incoming Discord message to webhook endpoint."""
        logger.debug(f"Discord: Forwarding message {message.id} to webhook endpoint")

        try:
            import httpx
            from config import settings

            # Use settings for base URL if available, otherwise default to localhost
            base_url = getattr(settings, "api_base_url", "http://localhost:8000")
            webhook_url = f"{base_url}/discord/webhook"

            logger.debug(f"   Webhook URL: {webhook_url}")

            payload = {
                "type": "message",
                "user_id": str(message.author.id),
                "channel_id": str(message.channel.id),
                "message_id": str(message.id),
                "content": message.content,
                "author": {
                    "id": str(message.author.id),
                    "username": message.author.name,
                },
                "username": message.author.name,
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                logger.debug(f"   Sending POST request to webhook...")
                response = await client.post(webhook_url, json=payload)

                if response.status_code == 200:
                    logger.info(
                        f"✓ Discord message {message.id} forwarded to webhook successfully"
                    )
                else:
                    logger.warning(f"✗ Failed to forward Discord message to webhook")
                    logger.warning(f"   Status code: {response.status_code}")
                    logger.warning(f"   Response: {response.text[:200]}")
        except httpx.TimeoutException:
            logger.error(
                f"✗ Discord webhook request timed out for message {message.id}"
            )
        except httpx.RequestError as e:
            logger.error(
                f"✗ Discord webhook request failed for message {message.id}: {e}"
            )
        except Exception as e:
            logger.error(
                f"✗ Error forwarding Discord message to webhook: {e}", exc_info=True
            )

    async def _forward_reaction_to_webhook(self, reaction, user, action: str = "add"):
        """Forward Discord reaction to webhook endpoint."""
        logger.debug(f"Discord: Forwarding reaction {action} to webhook endpoint")
        logger.debug(
            f"   Emoji: {reaction.emoji}, Message ID: {reaction.message.id}, User: {user.name}"
        )

        try:
            import httpx
            from config import settings

            # Use settings for base URL if available, otherwise default to localhost
            base_url = getattr(settings, "api_base_url", "http://localhost:8000")
            webhook_url = f"{base_url}/discord/webhook"

            logger.debug(f"   Webhook URL: {webhook_url}")

            # Get message content if available
            message_content = ""
            if hasattr(reaction.message, "content"):
                message_content = reaction.message.content

            payload = {
                "type": "reaction",
                "action": action,  # "add" or "remove"
                "user_id": str(user.id),
                "channel_id": str(reaction.message.channel.id),
                "message_id": str(reaction.message.id),
                "emoji": str(reaction.emoji),
                "emoji_name": (
                    reaction.emoji.name
                    if hasattr(reaction.emoji, "name")
                    else str(reaction.emoji)
                ),
                "author": {
                    "id": str(user.id),
                    "username": user.name,
                },
                "username": user.name,
                "message_content": message_content,
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                logger.debug(f"   Sending POST request to webhook...")
                response = await client.post(webhook_url, json=payload)

                if response.status_code == 200:
                    logger.info(
                        f"✓ Discord reaction ({action}) forwarded to webhook successfully"
                    )
                else:
                    logger.warning(f"✗ Failed to forward Discord reaction to webhook")
                    logger.warning(f"   Status code: {response.status_code}")
                    logger.warning(f"   Response: {response.text[:200]}")
        except httpx.TimeoutException:
            logger.error(f"✗ Discord webhook request timed out for reaction {action}")
        except httpx.RequestError as e:
            logger.error(f"✗ Discord webhook request failed for reaction {action}: {e}")
        except Exception as e:
            logger.error(
                f"✗ Error forwarding Discord reaction to webhook: {e}", exc_info=True
            )

    def is_configured(self) -> bool:
        """Check if Discord service is properly configured."""
        configured = self._bot_instance is not None and self.bot_token is not None
        logger.debug(
            f"Discord service configured check: {configured} (bot_instance={self._bot_instance is not None}, token={bool(self.bot_token)})"
        )
        return configured

    async def start_bot(self):
        """Start the Discord bot (should be run in a background task)."""
        logger.info("=" * 60)
        logger.info("Discord Bot: Starting...")
        logger.info("=" * 60)

        if not self.is_configured():
            logger.error("✗ Discord service not configured, cannot start bot")
            logger.error("   Check: DISCORD_BOT_TOKEN environment variable is set")
            logger.info("=" * 60)
            return

        if not self._bot_instance:
            logger.error("✗ Discord bot instance is None, cannot start")
            logger.error("   This indicates a problem during bot initialization")
            logger.info("=" * 60)
            return

        token_preview = (
            f"{self.bot_token[:10]}..." if len(self.bot_token) > 10 else "***"
        )
        logger.info(f"Bot token preview: {token_preview}")
        logger.debug(f"Bot instance exists: {self._bot_instance is not None}")
        logger.debug(f"Bot ready state before start: {self._bot_instance.is_ready()}")

        try:
            import discord

            logger.info("Calling bot.start() - this will block until bot connects...")
            logger.info("   Waiting for Discord API connection...")

            await self._bot_instance.start(self.bot_token)

            logger.warning("=" * 60)
            logger.warning("⚠ Discord bot.start() completed unexpectedly")
            logger.warning("   This usually means the bot disconnected")
            logger.warning("=" * 60)
        except discord.errors.LoginFailure as e:
            logger.error("=" * 60)
            logger.error("✗ DISCORD BOT LOGIN FAILED")
            logger.error("   Error: Invalid bot token")
            logger.error(f"   Details: {e}")
            logger.error("   Solution:")
            logger.error("   1. Verify DISCORD_BOT_TOKEN is correct")
            logger.error("   2. Check if token was reset in Discord Developer Portal")
            logger.error("   3. Ensure token has no extra spaces or quotes")
            logger.error("=" * 60)
        except discord.errors.PrivilegedIntentsRequired as e:
            logger.error("=" * 60)
            logger.error("✗ DISCORD BOT PRIVILEGED INTENTS REQUIRED")
            logger.error(f"   Error: {e}")
            logger.error("   Solution:")
            logger.error("   1. Go to Discord Developer Portal")
            logger.error("   2. Navigate to Bot → Privileged Gateway Intents")
            logger.error("   3. Enable 'MESSAGE CONTENT INTENT'")
            logger.error("=" * 60)
        except Exception as e:
            error_type = type(e).__name__
            logger.error("=" * 60)
            logger.error(f"✗ DISCORD BOT START FAILED")
            logger.error(f"   Error type: {error_type}")
            logger.error(f"   Error message: {e}")
            logger.error("=" * 60, exc_info=True)

    async def stop_bot(self):
        """Stop the Discord bot."""
        if self._bot_instance:
            await self._bot_instance.close()

    async def send_message_to_channel(
        self,
        channel_id: int,
        message: str,
        *,
        initiated_by_user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
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

        context_id = str(uuid.uuid4())
        message_preview = (
            message.strip().splitlines()[0][:120] if message.strip() else ""
        )
        self._message_contexts[context_id] = {
            "channel_id": channel_id,
            "initiated_by_user_id": initiated_by_user_id,
            "metadata": metadata or {},
            "message_preview": message_preview,
            "created_at": datetime.utcnow(),
            "responses": [],  # Track all responses to this message
        }

        try:
            import discord

            # Ensure bot is ready before proceeding
            if not await self._ensure_bot_ready(max_wait_seconds=30):
                logger.error("Discord bot is not ready, cannot send message")
                self._message_contexts.pop(context_id, None)
                return None

            # Get channel - try both get_channel and fetch_channel
            logger.debug(f"Attempting to get Discord channel {channel_id}")
            channel = self._bot_instance.get_channel(channel_id)
            logger.debug(
                f"get_channel() result: {channel} (type: {type(channel).__name__ if channel else None})"
            )

            if not channel:
                # Try fetching the channel
                logger.debug(
                    f"Channel not found in cache, attempting fetch_channel()..."
                )
                try:
                    channel = await self._bot_instance.fetch_channel(channel_id)
                    logger.debug(
                        f"fetch_channel() successful: {channel} (type: {type(channel).__name__})"
                    )
                except discord.errors.Forbidden as fetch_error:
                    logger.error(
                        f"Discord bot lacks permission to access channel {channel_id}: {fetch_error}"
                    )
                    self._message_contexts.pop(context_id, None)
                    return None
                except discord.errors.NotFound as fetch_error:
                    logger.error(
                        f"Discord channel {channel_id} not found: {fetch_error}"
                    )
                    self._message_contexts.pop(context_id, None)
                    return None
                except Exception as fetch_error:
                    logger.error(
                        f"Error fetching Discord channel {channel_id}: {fetch_error}",
                        exc_info=True,
                    )
                    self._message_contexts.pop(context_id, None)
                    return None

            if not channel:
                logger.error(
                    f"Discord channel {channel_id} not found or not accessible after all attempts"
                )
                self._message_contexts.pop(context_id, None)
                return None

            logger.info(
                f"Sending message to Discord channel {channel_id} ({channel.name if hasattr(channel, 'name') else 'unknown'})"
            )

            view = discord.ui.View(timeout=None)

            async def yes_callback(interaction: discord.Interaction):
                await self._handle_generic_button_response(
                    interaction=interaction,
                    context_id=context_id,
                    response="yes",
                )

            async def no_callback(interaction: discord.Interaction):
                await self._handle_generic_button_response(
                    interaction=interaction,
                    context_id=context_id,
                    response="no",
                )

            yes_button = discord.ui.Button(
                label="✅ Yes",
                style=discord.ButtonStyle.success,
                custom_id=f"msg_{context_id}_yes",
            )
            no_button = discord.ui.Button(
                label="❌ No",
                style=discord.ButtonStyle.danger,
                custom_id=f"msg_{context_id}_no",
            )

            yes_button.callback = yes_callback
            no_button.callback = no_callback

            view.add_item(yes_button)
            view.add_item(no_button)

            try:
                sent_message = await channel.send(message, view=view)
                logger.info(
                    f"Discord message sent successfully to channel {channel_id}: message ID {sent_message.id}"
                )
                self._message_contexts[context_id]["message_id"] = sent_message.id
                # Return dict with both message_id and context_id for agent to track responses
                return {
                    "message_id": sent_message.id,
                    "context_id": context_id,
                }
            except discord.errors.Forbidden as send_error:
                logger.error(
                    f"Discord bot lacks permission to send messages to channel {channel_id}: {send_error}"
                )
                logger.error("Check bot permissions: Send Messages, View Channels")
                self._message_contexts.pop(context_id, None)
                return None
            except Exception as send_error:
                logger.error(
                    f"Error sending message to Discord channel {channel_id}: {send_error}",
                    exc_info=True,
                )
                self._message_contexts.pop(context_id, None)
                return None

        except discord.errors.Forbidden as e:
            logger.error(
                f"Discord bot lacks permission to send messages to channel {channel_id}: {e}"
            )
            logger.error(
                "Required permissions: Send Messages, View Channels, Read Message History"
            )
            self._message_contexts.pop(context_id, None)
            return None
        except discord.errors.NotFound as e:
            logger.error(f"Discord channel {channel_id} not found: {e}")
            logger.error(
                "Verify the channel ID is correct and the bot has access to the channel"
            )
            self._message_contexts.pop(context_id, None)
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error sending Discord message to channel {channel_id}: {e}",
                exc_info=True,
            )
            self._message_contexts.pop(context_id, None)
            return None

    async def send_to_household(
        self,
        household_id: str,
        message: str,
        *,
        initiated_by_user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Optional[Union[int, str]]]:
        """
        Send a Discord message to the household's Discord channel.

        Args:
            household_id: ID of the household
            message: Message content to send

        Returns:
            Dict mapping user_id to message ID (or None if failed)
        """
        # Get household
        household = await Household.find_one(Household.household_id == household_id)
        if not household:
            logger.error(f"Household not found: {household_id}")
            return {}

        webhook_url = getattr(household, "discord_webhook_url", None)
        bot_available = self.is_configured()

        if not bot_available and not webhook_url:
            logger.warning("Discord service not configured and no webhook available")
            return {}

        if not household.discord_channel_id and not webhook_url:
            logger.warning(
                f"Household {household_id} has no Discord channel or webhook configured"
            )
            return {}

        message_id: Optional[Union[int, str]] = None
        context_id: Optional[str] = None
        metadata = dict(metadata or {})
        if initiated_by_user_id:
            metadata.setdefault("initiated_by_user_id", initiated_by_user_id)

        # Try sending via bot if available and channel configured
        if bot_available and household.discord_channel_id:
            result = await self.send_message_to_channel(
                int(household.discord_channel_id),
                message,
                initiated_by_user_id=metadata.get("initiated_by_user_id"),
                metadata=metadata,
            )
            # Handle both old format (int) and new format (dict)
            if isinstance(result, dict):
                message_id = result.get("message_id")
                context_id = result.get("context_id")
            else:
                message_id = result

        # Fallback to webhook if bot send failed or bot/channel unavailable
        if (message_id is None) and webhook_url:
            logger.info(
                "Falling back to Discord webhook for message delivery (interactive buttons unavailable)"
            )
            webhook_sent = await self._send_message_via_webhook(webhook_url, message)
            if webhook_sent:
                message_id = "webhook"

        # Return results for all household members
        results = {}
        if household.member_ids:
            for member_id in household.member_ids:
                results[member_id] = message_id
        else:
            results["household"] = message_id
        
        # Add context_id to results if available
        if context_id:
            results["context_id"] = context_id

        return results

    async def _send_message_via_webhook(
        self,
        webhook_url: str,
        message: str,
    ) -> bool:
        """
        Send a message using a Discord webhook.

        Args:
            webhook_url: Discord webhook URL
            message: Message content to send

        Returns:
            True if the message was accepted by Discord, False otherwise.
        """
        if not webhook_url:
            return False

        logger.info("Attempting to send Discord message via webhook")
        logger.debug(f"Webhook URL (preview): {webhook_url[:80]}...")
        logger.debug(f"Webhook message content (first 50 chars): {message[:50]}...")

        try:
            import httpx

            payload = {"content": message}
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(webhook_url, json=payload)

            if 200 <= response.status_code < 300:
                logger.info("Discord webhook message sent successfully")
                return True

            logger.error(
                "Failed to send Discord webhook message "
                f"(status={response.status_code}, response={response.text[:200]})"
            )
            return False
        except httpx.TimeoutException:
            logger.error("Discord webhook request timed out")
            return False
        except httpx.RequestError as e:
            logger.error(f"Discord webhook request failed: {e}")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error sending Discord webhook message: {e}", exc_info=True
            )
            return False

    async def _handle_generic_button_response(
        self,
        interaction,
        context_id: str,
        response: str,
    ):
        """
        Handle YES/NO button interactions for regular Discord messages.
        """
        logger.info("=" * 60)
        logger.info("Discord: Generic button interaction received")
        logger.info(f"   Context ID: {context_id}")
        logger.info(f"   Response: {response}")
        logger.info("=" * 60)

        context = self._message_contexts.get(context_id)
        if not context:
            logger.warning(f"No interaction context found for context_id={context_id}")
            try:
                await interaction.response.send_message(
                    "❌ This prompt is no longer active.",
                    ephemeral=True,
                )
            except Exception:
                pass
            return

        try:
            import discord

            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            logger.debug(
                "Discord: Unable to defer interaction response (possibly already deferred)"
            )

        discord_user_id = str(interaction.user.id)
        user = await User.find_one(User.discord_user_id == discord_user_id)

        if not user:
            logger.error(
                f"Discord user {discord_user_id} not linked to any system user"
            )
            try:
                await interaction.followup.send(
                    "❌ We couldn't link your Discord account to a user profile. "
                    "Please ensure your Discord ID is saved in your settings.",
                    ephemeral=True,
                )
            except Exception:
                pass
            return

        response_text = "YES" if response == "yes" else "NO"
        initiated_by_user_id = context.get("initiated_by_user_id")
        message_preview = context.get("message_preview", "")

        logger.info(f"Discord response recorded: {user.name} => {response_text}")

        # Store response in context
        response_data = {
            "user_id": user.user_id,
            "user_name": user.name,
            "response": response_text,
            "response_lower": response,  # "yes" or "no"
            "timestamp": datetime.utcnow(),
        }
        if "responses" not in context:
            context["responses"] = []
        context["responses"].append(response_data)

        if initiated_by_user_id:
            try:
                from api.dependencies import agent as shared_agent

                await shared_agent.add_message_to_conversation(
                    user_id=initiated_by_user_id,
                    message=(
                        f"[Discord] {user.name} responded '{response_text}' "
                        f'to your message: "{message_preview}"'
                    ),
                    role="user",
                )
                logger.debug("Discord: Response relayed to agent conversation")
            except Exception as e:
                logger.warning(
                    f"Failed to relay Discord response to agent conversation: {e}",
                    exc_info=True,
                )

        try:
            await interaction.followup.send(
                f"✅ Thanks {user.name}! Recorded your response: {response_text}.",
                ephemeral=True,
            )
        except Exception as e:
            logger.debug(f"Unable to send follow-up confirmation: {e}")

    async def get_message_responses(
        self,
        context_id: Optional[str] = None,
        message_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get responses to a Discord message.
        
        Args:
            context_id: The context ID of the message (preferred)
            message_id: The Discord message ID (alternative lookup)
            user_id: Filter responses by user who initiated the message
            
        Returns:
            Dict with message info and responses
        """
        # Find context by context_id or message_id
        context = None
        if context_id:
            context = self._message_contexts.get(context_id)
        elif message_id:
            # Search for context with matching message_id
            for ctx_id, ctx in self._message_contexts.items():
                if ctx.get("message_id") == message_id:
                    context = ctx
                    context_id = ctx_id
                    break
        
        if not context:
            return {
                "found": False,
                "error": "Message context not found. It may have expired or been cleared.",
            }
        
        # Filter by user_id if provided
        if user_id and context.get("initiated_by_user_id") != user_id:
            return {
                "found": False,
                "error": "Message was not initiated by the specified user.",
            }
        
        responses = context.get("responses", [])
        
        # Count responses by type
        yes_count = sum(1 for r in responses if r.get("response_lower") == "yes")
        no_count = sum(1 for r in responses if r.get("response_lower") == "no")
        
        return {
            "found": True,
            "context_id": context_id,
            "message_id": context.get("message_id"),
            "message_preview": context.get("message_preview", ""),
            "created_at": context.get("created_at").isoformat() if context.get("created_at") else None,
            "total_responses": len(responses),
            "yes_count": yes_count,
            "no_count": no_count,
            "responses": [
                {
                    "user_name": r.get("user_name"),
                    "user_id": r.get("user_id"),
                    "response": r.get("response"),
                    "timestamp": r.get("timestamp").isoformat() if r.get("timestamp") else None,
                }
                for r in responses
            ],
        }

    async def _ensure_bot_ready(self, max_wait_seconds: int = 30) -> bool:
        """
        Ensure Discord bot is ready before sending messages.

        Args:
            max_wait_seconds: Maximum time to wait for bot to be ready

        Returns:
            True if bot is ready, False otherwise
        """
        if not self._bot_instance:
            logger.error("Discord bot instance is None")
            return False

        if self._bot_instance.is_ready():
            return True

        logger.info(
            f"Discord bot not ready yet, waiting up to {max_wait_seconds} seconds..."
        )
        import asyncio

        # Wait in smaller increments for better responsiveness
        wait_interval = 0.5
        max_iterations = int(max_wait_seconds / wait_interval)

        for i in range(max_iterations):
            await asyncio.sleep(wait_interval)
            if self._bot_instance.is_ready():
                logger.info(
                    f"Discord bot became ready after {i * wait_interval:.1f} seconds"
                )
                return True

            # Log progress every 5 seconds
            if i > 0 and i % 10 == 0:
                logger.debug(
                    f"Still waiting for Discord bot... ({i * wait_interval:.1f}s elapsed)"
                )

        logger.error(
            f"Discord bot did not become ready within {max_wait_seconds} seconds"
        )
        logger.error(
            f"Bot state: is_ready()={self._bot_instance.is_ready()}, user={self._bot_instance.user}"
        )
        return False

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
        logger.info("=" * 60)
        logger.info(f"Discord: Sending group order notification")
        logger.info(f"   Order ID: {order_id}")
        logger.info(f"   Household ID: {household_id}")
        logger.info(f"   Items count: {len(items)}")
        logger.info("=" * 60)

        if not self.is_configured():
            logger.error(
                "✗ Discord service not configured, cannot send group order notification"
            )
            logger.error("   Check: DISCORD_BOT_TOKEN environment variable is set")
            return False

        try:
            import discord

            # Ensure bot is ready before proceeding
            logger.info("Checking Discord bot readiness...")
            if not await self._ensure_bot_ready(max_wait_seconds=30):
                logger.error(
                    "✗ Discord bot is not ready, cannot send group order notification"
                )
                logger.error("   The bot may not be connected to Discord")
                return False
            logger.info("✓ Discord bot is ready")

            # Get household
            logger.debug(f"Fetching household: {household_id}")
            household = await Household.find_one(Household.household_id == household_id)
            if not household:
                logger.error(f"✗ Household {household_id} not found in database")
                return False

            if not household.discord_channel_id:
                logger.error(
                    f"✗ Household {household_id} has no Discord channel configured"
                )
                logger.error("   Set discord_channel_id in household record")
                return False

            logger.info(
                f"✓ Household found with Discord channel: {household.discord_channel_id}"
            )

            # Get creator's name
            logger.debug(f"Fetching creator user: {created_by_user}")
            creator = await User.find_one(User.user_id == created_by_user)
            creator_name = creator.name if creator else "Someone"
            logger.info(f"   Order created by: {creator_name}")

            # Format deadline
            deadline_str = response_deadline.strftime("%Y-%m-%d %H:%M")
            logger.debug(f"   Response deadline: {deadline_str}")

            # Calculate total price for items
            total_price = sum(
                item.get("price", 0) * item.get("quantity", 0)
                for item in items
                if item.get("price")
            )
            logger.debug(f"   Total price: €{total_price:.2f}")

            # Build message with Discord formatting
            message_lines = [
                f"🛒 **New Group Order**",
                f"",
                f"Created by: **{creator_name}**",
                f"",
                f"**Items:**",
            ]

            for item in items:
                item_name = item.get("name", "Unknown")
                quantity = item.get("quantity", 0)
                unit = item.get("unit", "")
                price = item.get("price", 0)
                if price:
                    item_total = price * quantity
                    message_lines.append(
                        f"• {item_name}: {quantity} {unit} (€{item_total:.2f})"
                    )
                else:
                    message_lines.append(f"• {item_name}: {quantity} {unit}")

            if total_price > 0:
                message_lines.append(f"")
                message_lines.append(f"**Estimated Total:** €{total_price:.2f}")

            message_lines.extend(
                [
                    f"",
                    f"**Do you need these items?** Click a button below to respond.",
                    f"",
                    f"⏰ Deadline: {deadline_str}",
                    f"",
                    f"Order ID: `{order_id}`",
                ]
            )

            message_content = "\n".join(message_lines)

            # Create Discord View with buttons
            view = discord.ui.View(timeout=None)  # No timeout - buttons stay active

            # YES button - user wants the items
            yes_button = discord.ui.Button(
                label="✅ YES, I need these",
                style=discord.ButtonStyle.success,
                custom_id=f"order_{order_id}_yes",
            )

            # NO button - user doesn't need the items
            no_button = discord.ui.Button(
                label="❌ NO, I don't need these",
                style=discord.ButtonStyle.danger,
                custom_id=f"order_{order_id}_no",
            )

            # Add button callbacks
            async def yes_callback(interaction: discord.Interaction):
                await self._handle_order_button_response(
                    interaction=interaction, order_id=order_id, response="yes"
                )

            async def no_callback(interaction: discord.Interaction):
                await self._handle_order_button_response(
                    interaction=interaction, order_id=order_id, response="no"
                )

            yes_button.callback = yes_callback
            no_button.callback = no_callback

            view.add_item(yes_button)
            view.add_item(no_button)

            # Get channel and send message with buttons
            channel_id = int(household.discord_channel_id)
            logger.info(f"Getting Discord channel: {channel_id}")

            channel = self._bot_instance.get_channel(channel_id)

            if not channel:
                try:
                    logger.debug(
                        f"   Channel {channel_id} not in cache, fetching from Discord API..."
                    )
                    channel = await self._bot_instance.fetch_channel(channel_id)
                    logger.info(
                        f"✓ Successfully fetched channel {channel_id} from Discord API"
                    )
                    logger.debug(
                        f"   Channel name: {channel.name if hasattr(channel, 'name') else 'unknown'}"
                    )
                except discord.errors.Forbidden as e:
                    logger.error("=" * 60)
                    logger.error("✗ DISCORD PERMISSION ERROR: Cannot access channel")
                    logger.error(f"   Channel ID: {channel_id}")
                    logger.error(f"   Error: {e}")
                    logger.error("   Solution:")
                    logger.error("   1. Ensure bot is invited to the server")
                    logger.error("   2. Check bot has 'View Channels' permission")
                    logger.error("   3. Verify channel ID is correct")
                    logger.error("=" * 60)
                    return False
                except discord.errors.NotFound as e:
                    logger.error("=" * 60)
                    logger.error("✗ DISCORD CHANNEL NOT FOUND")
                    logger.error(f"   Channel ID: {channel_id}")
                    logger.error(f"   Error: {e}")
                    logger.error("   Solution:")
                    logger.error("   1. Verify channel ID is correct")
                    logger.error("   2. Ensure bot has access to the channel")
                    logger.error("   3. Check if channel was deleted")
                    logger.error("=" * 60)
                    return False
                except Exception as e:
                    logger.error("=" * 60)
                    logger.error("✗ ERROR FETCHING DISCORD CHANNEL")
                    logger.error(f"   Channel ID: {channel_id}")
                    logger.error(f"   Error type: {type(e).__name__}")
                    logger.error(f"   Error: {e}")
                    logger.error("=" * 60, exc_info=True)
                    return False

            if not channel:
                logger.error(
                    f"✗ Discord channel {channel_id} not found or not accessible after all attempts"
                )
                return False

            logger.info(
                f"✓ Channel accessible: {channel.name if hasattr(channel, 'name') else 'unknown'}"
            )

            # Send message with buttons
            logger.info("Sending group order notification message...")
            try:
                sent_message = await channel.send(content=message_content, view=view)
                logger.info("=" * 60)
                logger.info("✓ DISCORD GROUP ORDER NOTIFICATION SENT SUCCESSFULLY")
                logger.info(f"   Order ID: {order_id}")
                logger.info(f"   Message ID: {sent_message.id}")
                logger.info(
                    f"   Channel: {channel.name if hasattr(channel, 'name') else 'unknown'}"
                )
                logger.info("=" * 60)

                # Optionally add reactions for additional tracking
                logger.debug("Adding reactions to message...")
                try:
                    await sent_message.add_reaction("✅")
                    await sent_message.add_reaction("❌")
                    logger.debug("✓ Reactions added successfully")
                except discord.errors.Forbidden as reaction_error:
                    logger.warning(
                        f"⚠ Could not add reactions: Bot lacks 'Add Reactions' permission"
                    )
                    logger.warning(f"   Error: {reaction_error}")
                except Exception as reaction_error:
                    logger.warning(
                        f"⚠ Could not add reactions to message: {reaction_error}"
                    )

                return True
            except discord.errors.Forbidden as e:
                logger.error("=" * 60)
                logger.error("✗ DISCORD PERMISSION ERROR: Cannot send message")
                logger.error(f"   Channel ID: {channel_id}")
                logger.error(f"   Error: {e}")
                logger.error("   Required permissions:")
                logger.error("   - Send Messages")
                logger.error("   - View Channels")
                logger.error("   - Use External Emojis (for reactions)")
                logger.error("=" * 60)
                return False
            except Exception as e:
                logger.error("=" * 60)
                logger.error("✗ ERROR SENDING DISCORD MESSAGE")
                logger.error(f"   Channel ID: {channel_id}")
                logger.error(f"   Order ID: {order_id}")
                logger.error(f"   Error type: {type(e).__name__}")
                logger.error(f"   Error: {e}")
                logger.error("=" * 60, exc_info=True)
                return False

        except Exception as e:
            logger.error("=" * 60)
            logger.error("✗ FAILED TO SEND DISCORD GROUP ORDER NOTIFICATION")
            logger.error(f"   Order ID: {order_id}")
            logger.error(f"   Household ID: {household_id}")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error: {e}")
            logger.error("=" * 60, exc_info=True)
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
        logger.info("=" * 60)
        logger.info(f"Discord: Button interaction received")
        logger.info(f"   Order ID: {order_id}")
        logger.info(f"   Response: {response}")
        logger.info("=" * 60)

        try:
            import discord

            # Acknowledge the interaction immediately
            logger.debug("Acknowledging interaction...")
            await interaction.response.defer(ephemeral=True)
            logger.debug("✓ Interaction acknowledged")

            # Get user info
            discord_user_id = str(interaction.user.id)
            channel_id = str(interaction.channel.id)
            user_name = interaction.user.name

            logger.info(f"   User: {user_name} (Discord ID: {discord_user_id})")
            logger.info(f"   Channel: {channel_id}")

            # Find user by Discord ID
            logger.debug(f"Looking up user by Discord ID: {discord_user_id}")
            user = await User.find_one(User.discord_user_id == discord_user_id)

            if not user:
                logger.debug(
                    f"User not found by Discord ID, trying to find by channel and name..."
                )
                # Try to find by channel and name
                from models.household import Household

                household = await Household.find_one(
                    Household.discord_channel_id == channel_id
                )
                if household:
                    logger.debug(
                        f"Found household {household.household_id} for channel {channel_id}"
                    )
                    users = await User.find(
                        User.household_id == household.household_id,
                        User.is_active == True,
                    ).to_list()
                    logger.debug(
                        f"Found {len(users)} users in household, matching by name..."
                    )
                    for u in users:
                        if u.name.lower() == user_name.lower():
                            user = u
                            logger.info(
                                f"✓ Matched user by name: {u.name} (User ID: {u.user_id})"
                            )
                            if not u.discord_user_id:
                                u.discord_user_id = discord_user_id
                                await u.save()
                                logger.info(
                                    f"✓ Updated user {u.user_id} with Discord ID: {discord_user_id}"
                                )
                            break

            if not user:
                logger.error(
                    f"✗ User not found for Discord user {user_name} (ID: {discord_user_id})"
                )
                logger.error(
                    "   User needs to have their Discord user ID set in their profile"
                )
                await interaction.followup.send(
                    "❌ User not found. Please ensure your Discord user ID is set in your profile.",
                    ephemeral=True,
                )
                return

            logger.info(f"✓ User found: {user.name} (User ID: {user.user_id})")

            # Find the order
            logger.debug(f"Looking up order: {order_id}")
            from models.order import Order, OrderStatus

            order = await Order.find_one(Order.order_id == order_id)

            if not order:
                logger.error(f"✗ Order {order_id} not found in database")
                await interaction.followup.send(
                    f"❌ Order {order_id} not found.", ephemeral=True
                )
                return

            logger.info(f"✓ Order found: {order_id} (Status: {order.status})")

            # Check if user needs to respond
            user_needs_to_respond = False
            pending_item_names = []
            for item_name, pending_users in order.pending_responses.items():
                if user.user_id in pending_users:
                    user_needs_to_respond = True
                    pending_item_names.append(item_name)

            if not user_needs_to_respond:
                await interaction.followup.send(
                    "✅ You've already responded to this order.", ephemeral=True
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
                            "unit": item.unit,
                        }
                        for item in order.items
                        if item.name in pending_item_names
                    ],
                }
                confirmation_msg = f"✅ Added to order: {', '.join(pending_item_names)}"
            else:  # "no"
                # User doesn't need the items
                parsed_response = {"confirmed": False, "items": []}
                confirmation_msg = "✅ Noted - you don't need these items."

            # Process the response via ordering service
            from modules.ordering import OrderingService

            ordering_service = OrderingService()
            response_event = {
                "order_id": order_id,
                "user_id": user.user_id,
                "user_name": user.name,
                "response": response,
                "confirmed": parsed_response.get("confirmed"),
                "items": parsed_response.get("items", []),
                "channel_id": channel_id,
                "discord_message_id": getattr(interaction.message, "id", None),
                "source": "discord",
                "summary": confirmation_msg,
            }
            updated_order = await ordering_service.process_group_order_response(
                order_id=order_id,
                user_id=user.user_id,
                responses=parsed_response,
                response_event=response_event,
            )

            if updated_order:
                logger.info(f"✓ Order response processed successfully")

                # Send public confirmation in channel
                logger.debug("Sending public confirmation to channel...")
                try:
                    from models.household import Household

                    household = await Household.find_one(
                        Household.household_id == user.household_id
                    )
                    if household and household.discord_channel_id:
                        channel = self._bot_instance.get_channel(
                            int(household.discord_channel_id)
                        )
                        if channel:
                            await channel.send(f"**{user.name}**: {confirmation_msg}")
                            logger.debug("✓ Public confirmation sent to channel")
                except Exception as e:
                    logger.warning(f"⚠ Failed to send public confirmation: {e}")

                # Relay response back to agent conversations
                logger.debug("Relaying response to agent conversations...")
                try:
                    from api.dependencies import agent

                    response_label = "YES" if response == "yes" else "NO"
                    response_items = (
                        parsed_response.get("items", [])
                        if isinstance(parsed_response, dict)
                        else []
                    )
                    items_summary = ", ".join(
                        f"{item.get('name', 'unknown')} ({item.get('quantity', 0):g} {item.get('unit', '').strip()})"
                        for item in response_items
                        if item.get("name")
                    )

                    agent_message_parts = [
                        f"[Discord] {user.name} responded {response_label} to group order `{order_id}`."
                    ]
                    if items_summary:
                        agent_message_parts.append(f"Items selected: {items_summary}.")
                    if updated_order.status == OrderStatus.CONFIRMED:
                        order_totals = ", ".join(
                            f"{oi.name} ({oi.quantity:g} {oi.unit})"
                            for oi in updated_order.items
                        )
                        agent_message_parts.append(
                            "Order is now confirmed."
                            f" Updated totals: {order_totals}. Total cost: €{updated_order.total:.2f}."
                        )
                    agent_message = " ".join(agent_message_parts)

                    await agent.add_message_to_conversation(
                        user_id=user.user_id, message=agent_message, role="user"
                    )

                    if order.created_by and order.created_by != user.user_id:
                        await agent.add_message_to_conversation(
                            user_id=order.created_by, message=agent_message, role="user"
                        )
                        logger.debug("✓ Response relayed to order creator conversation")

                    logger.debug("✓ Response relayed to agent conversation(s)")
                except Exception as e:
                    logger.warning(
                        f"⚠ Failed to relay response to agent conversations: {e}"
                    )

                # Send ephemeral confirmation to user
                logger.debug("Sending ephemeral confirmation to user...")
                await interaction.followup.send(confirmation_msg, ephemeral=True)

                logger.info("=" * 60)
                logger.info("✓ DISCORD BUTTON RESPONSE PROCESSED SUCCESSFULLY")
                logger.info(f"   Order ID: {order_id}")
                logger.info(f"   User: {user.name} ({user.user_id})")
                logger.info(f"   Response: {response}")
                logger.info("=" * 60)
            else:
                logger.error(f"✗ Failed to process order response for order {order_id}")
                await interaction.followup.send(
                    "❌ Failed to process your response. Please try again.",
                    ephemeral=True,
                )

        except Exception as e:
            logger.error("=" * 60)
            logger.error("✗ ERROR HANDLING DISCORD BUTTON RESPONSE")
            logger.error(f"   Order ID: {order_id}")
            logger.error(f"   Response: {response}")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error: {e}")
            logger.error("=" * 60, exc_info=True)
            try:
                await interaction.followup.send(
                    "❌ An error occurred processing your response.", ephemeral=True
                )
            except Exception as followup_error:
                logger.error(
                    f"✗ Also failed to send error message to user: {followup_error}"
                )

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
        self, message: str, order_items: List[Dict[str, Any]]
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
        if any(
            word in message_lower for word in ["yes", "confirm", "add me", "i need"]
        ):
            # User wants all items
            return {
                "items": [
                    {"name": item.get("name"), "quantity": item.get("quantity", 1.0)}
                    for item in order_items
                ],
                "confirmed": True,
            }

        # Check for explicit rejections
        if any(word in message_lower for word in ["no", "skip", "pass", "not needed"]):
            return {"items": [], "confirmed": False}

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

                parsed_items.append({"name": item.get("name"), "quantity": quantity})

        return {"items": parsed_items, "confirmed": len(parsed_items) > 0}

    def get_message_handler(self):
        """Get the bot instance for setting up message handlers."""
        return self._bot_instance
