"""
Command-Line Interface for the Grocery Management Agent.

Provides a text-based interface for interacting with the agent.
"""
import asyncio
import json
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
import httpx

from database import db
from agent.core import GroceryAgent
from models.user import User
from models.household import Household
from models.order import Order, OrderStatus
from config import settings


console = Console()


class GroceryCLI:
    """
    Interactive command-line interface for the grocery agent.
    """
    
    def __init__(self):
        """Initialize CLI."""
        self.agent = None
        self.running = False
        self.current_user: Optional[User] = None
        self.current_household: Optional[Household] = None
        self.api_base_url = "http://localhost:8000"
        self.processed_orders: set[str] = set()  # Track orders we've already processed
        self.last_message_count: dict[str, int] = {}  # Track last message count per user
        self.displayed_messages: dict[str, set[str]] = {}  # Track displayed messages per user
    
    async def start(self):
        """Start the CLI interface."""
        # Display welcome banner
        self._display_welcome()
        
        # Connect to database
        await self._setup_database()
        
        # Setup user and household
        await self._setup_user_and_household()
        
        # Initialize agent
        self.agent = GroceryAgent()
        
        # Main command loop
        self.running = True
        await self._command_loop()
    
    def _display_welcome(self):
        """Display welcome message."""
        welcome_text = """
# 🛒 Grocery Management Agent

Your intelligent assistant for shared flat grocery management.

**Available Commands:**
- Order groceries: "Order 2 liters of milk"
- Check inventory: "What's in the inventory?"
- Add items: "Add 5 eggs to inventory"
- Check low stock: "Show low stock items"
- Order status: "Show recent orders"
- Help: "help"
- Exit: "exit" or "quit"
        """
        
        console.print(Panel(Markdown(welcome_text), border_style="green"))
    
    async def _setup_database(self):
        """Setup database connection."""
        try:
            console.print("[yellow]Connecting to MongoDB...[/yellow]")
            await db.connect()
            console.print("[green]✓ Database connected[/green]\n")
        except Exception as e:
            console.print(f"[red]✗ Database connection failed: {e}[/red]")
            console.print("[yellow]Make sure MongoDB is running and configured correctly.[/yellow]")
            raise
    
    async def _setup_user_and_household(self):
        """Setup user identification and household context."""
        console.print("\n[bold cyan]Welcome to Yuyabre! 🛒[/bold cyan]")
        console.print("Let's get you set up.\n")
        
        # Check if there are existing users
        existing_users = await User.find_all().to_list()
        
        if existing_users:
            # Show existing users
            table = Table(title="Existing Users", show_header=True, header_style="bold magenta")
            table.add_column("Name", style="green")
            table.add_column("Email", style="yellow")
            table.add_column("Household", style="blue")
            
            for user in existing_users:
                household_name = "None"
                if user.household_id:
                    household = await Household.find_one(Household.household_id == user.household_id)
                    if household:
                        household_name = household.name
                
                table.add_row(
                    user.name,
                    user.email or "N/A",
                    household_name
                )
            
            console.print(table)
            console.print()
            
            login_choice = Prompt.ask(
                "Are you a [bold]new user[/bold] or do you want to [bold]login[/bold]?",
                choices=["new", "login"],
                default="login"
            )
            
            if login_choice == "login":
                username_input = Prompt.ask("Enter your name or email to login")
                
                # Try to find by name first, then by email
                user = await User.find_one(User.name == username_input)
                if not user:
                    user = await User.find_one(User.email == username_input)
                
                if user:
                    self.current_user = user
                    console.print(f"[green]✓ Welcome back, {user.name}![/green]")
                    
                    # Check if Discord user ID is missing
                    if not self.current_user.discord_user_id:
                        console.print("\n[bold yellow]Discord Integration[/bold yellow]")
                        
                        # Check if Discord bot token is configured
                        discord_configured = bool(settings.discord_bot_token)
                        if not discord_configured:
                            console.print("[red]⚠ Warning: Discord bot token not configured in environment variables.[/red]")
                            console.print("[dim]Discord features will not work until DISCORD_BOT_TOKEN is set.[/dim]\n")
                        else:
                            console.print("[green]✓ Discord bot token is configured[/green]\n")
                        
                        console.print("Your Discord user ID is not set.")
                        console.print("This is needed for the bot to identify you when you respond to group orders.\n")
                        setup_discord = Confirm.ask(
                            "Would you like to add your Discord user ID now? (Recommended for group orders)",
                            default=True
                        )
                        if setup_discord:
                            console.print("\n[cyan]How to find your Discord user ID:[/cyan]")
                            console.print("  1. Open Discord → User Settings → Advanced")
                            console.print("  2. Enable 'Developer Mode'")
                            console.print("  3. Right-click your name (in any server or DM)")
                            console.print("  4. Click 'Copy ID'\n")
                            
                            discord_user_id = Prompt.ask("Enter your Discord user ID", default="")
                            if discord_user_id:
                                self.current_user.discord_user_id = discord_user_id
                                await self.current_user.save()
                                console.print("[green]✓ Discord user ID saved![/green]")
                                
                                if not discord_configured:
                                    console.print("[yellow]⚠ Note: User ID saved, but Discord bot token is not configured.[/yellow]")
                                    console.print("[yellow]   Discord features will not work until DISCORD_BOT_TOKEN is set.[/yellow]\n")
                    
                    # Ask if they want to update preferences
                    update_prefs = Confirm.ask(
                        "\nDo you want to update your preferences?",
                        default=False
                    )
                    if update_prefs:
                        await self._collect_user_preferences(self.current_user)
                        await self.current_user.save()
                        console.print("[green]✓ Preferences updated![/green]")
                else:
                    console.print("[red]User not found. Let's create a new account.[/red]\n")
                    await self._create_new_user_with_preferences()
            else:
                await self._create_new_user_with_preferences()
        else:
            console.print("[yellow]No existing users found. Let's create your account.[/yellow]\n")
            await self._create_new_user_with_preferences()
        
        # Setup household
        await self._setup_household()
        
        console.print(f"\n[green]✓ Setup complete![/green]")
        console.print(f"[dim]User: {self.current_user.name} | Household: {self.current_household.name if self.current_household else 'None'}[/dim]\n")
    
    async def _create_new_user_with_preferences(self):
        """Create a new user with full profile setup."""
        console.print("[bold cyan]Creating Your Profile[/bold cyan]\n")
        
        # Basic information
        name = Prompt.ask("Enter your full name")
        email = Prompt.ask("Enter your email (optional)", default="")
        phone = Prompt.ask("Enter your phone number (optional, for WhatsApp)", default="")
        splitwise_id = Prompt.ask("Enter your Splitwise user ID (optional)", default="")
        
        # Discord user ID
        console.print("\n[bold yellow]Discord Integration[/bold yellow]")
        
        # Check if Discord bot token is configured
        discord_configured = bool(settings.discord_bot_token)
        if not discord_configured:
            console.print("[red]⚠ Warning: Discord bot token not configured in environment variables.[/red]")
            console.print("[dim]To enable Discord integration, set DISCORD_BOT_TOKEN in your .env file.[/dim]")
            console.print("[dim]See SETUP.md for instructions on creating a Discord bot.[/dim]\n")
        else:
            console.print("[green]✓ Discord bot token is configured[/green]\n")
        
        console.print("To receive and respond to group orders via Discord, you need to provide your Discord user ID.")
        console.print("This allows the bot to identify you when you click buttons or send messages.\n")
        console.print("[cyan]How to find your Discord user ID:[/cyan]")
        console.print("  1. Open Discord → User Settings → Advanced")
        console.print("  2. Enable 'Developer Mode'")
        console.print("  3. Right-click your name (in any server or DM)")
        console.print("  4. Click 'Copy ID'\n")
        
        discord_user_id = Prompt.ask("Enter your Discord user ID (recommended if using Discord)", default="")
        
        if discord_user_id and not discord_configured:
            console.print("[yellow]⚠ Note: You've entered a Discord user ID, but Discord bot token is not configured.[/yellow]")
            console.print("[yellow]   Discord features will not work until DISCORD_BOT_TOKEN is set.[/yellow]\n")
        
        # Create user
        user = User(
            name=name,
            email=email if email else None,
            phone=phone if phone else None,
            splitwise_user_id=splitwise_id if splitwise_id else None,
            discord_user_id=discord_user_id if discord_user_id else None,
        )
        
        # Collect preferences
        await self._collect_user_preferences(user)
        
        # Save user
        await user.insert()
        self.current_user = user
        console.print(f"\n[green]✓ Profile created: {user.name}[/green]")
    
    async def _collect_user_preferences(self, user: User):
        """Collect user dietary preferences and restrictions."""
        console.print("\n[bold cyan]Dietary Preferences[/bold cyan]")
        console.print("Let's learn about your dietary needs and preferences.\n")
        
        # Dietary restrictions
        console.print("[yellow]Dietary Restrictions[/yellow]")
        console.print("Common options: vegetarian, vegan, pescatarian, halal, kosher, etc.")
        restrictions_input = Prompt.ask(
            "Enter dietary restrictions (comma-separated, or press Enter to skip)",
            default=""
        )
        if restrictions_input:
            user.preferences.dietary_restrictions = [
                r.strip() for r in restrictions_input.split(",") if r.strip()
            ]
        
        # Allergies
        console.print("\n[yellow]Allergies[/yellow]")
        console.print("Common allergies: nuts, gluten, dairy, eggs, shellfish, etc.")
        allergies_input = Prompt.ask(
            "Enter allergies (comma-separated, or press Enter to skip)",
            default=""
        )
        if allergies_input:
            user.preferences.allergies = [
                a.strip() for a in allergies_input.split(",") if a.strip()
            ]
        
        # Favorite brands
        console.print("\n[yellow]Favorite Brands[/yellow]")
        console.print("Brands you prefer for groceries (e.g., Melkunie, Albert Heijn, etc.)")
        brands_input = Prompt.ask(
            "Enter favorite brands (comma-separated, or press Enter to skip)",
            default=""
        )
        if brands_input:
            user.preferences.favorite_brands = [
                b.strip() for b in brands_input.split(",") if b.strip()
            ]
        
        # Disliked items
        console.print("\n[yellow]Disliked Items[/yellow]")
        console.print("Items you don't want in orders (e.g., brussels sprouts, cilantro, etc.)")
        disliked_input = Prompt.ask(
            "Enter disliked items (comma-separated, or press Enter to skip)",
            default=""
        )
        if disliked_input:
            user.preferences.disliked_items = [
                d.strip() for d in disliked_input.split(",") if d.strip()
            ]
        
        # Summary
        console.print("\n[bold green]Preferences Summary:[/bold green]")
        if user.preferences.dietary_restrictions:
            console.print(f"  Dietary Restrictions: {', '.join(user.preferences.dietary_restrictions)}")
        if user.preferences.allergies:
            console.print(f"  Allergies: {', '.join(user.preferences.allergies)}")
        if user.preferences.favorite_brands:
            console.print(f"  Favorite Brands: {', '.join(user.preferences.favorite_brands)}")
        if user.preferences.disliked_items:
            console.print(f"  Disliked Items: {', '.join(user.preferences.disliked_items)}")
        
        if not any([
            user.preferences.dietary_restrictions,
            user.preferences.allergies,
            user.preferences.favorite_brands,
            user.preferences.disliked_items
        ]):
            console.print("  [dim]No preferences set (you can update these later)[/dim]")
        
        console.print()
    
    async def _setup_household(self):
        """Setup household for the user."""
        # Check if user already has a household
        if self.current_user.household_id:
            household = await Household.find_one(
                Household.household_id == self.current_user.household_id
            )
            if household:
                self.current_household = household
                console.print(f"[green]✓ Using household: {household.name}[/green]")
                return
        
        # Check if there are existing households
        existing_households = await Household.find_all().to_list()
        
        if existing_households:
            table = Table(title="Existing Households", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="green")
            table.add_column("Members", style="yellow")
            
            for household in existing_households:
                member_count = len(household.member_ids)
                table.add_row(
                    household.household_id[:8] + "...",
                    household.name,
                    str(member_count)
                )
            
            console.print(table)
            console.print()
            
            join_existing = Confirm.ask("Do you want to join an existing household?", default=True)
            
            if join_existing:
                household_id_input = Prompt.ask(
                    "Enter household ID (or name) to join",
                    default=existing_households[0].household_id if existing_households else None
                )
                
                # Try to find by ID first, then by name
                household = await Household.find_one(Household.household_id == household_id_input)
                if not household:
                    household = await Household.find_one(Household.name == household_id_input)
                
                if household:
                    # Add user to household
                    household.add_member(self.current_user.user_id)
                    
                    # Check if household needs Discord channel configured
                    if not household.discord_channel_id:
                        console.print("\n[bold yellow]Discord Channel Setup[/bold yellow]")
                        
                        # Check if Discord bot token is configured
                        discord_configured = bool(settings.discord_bot_token)
                        if not discord_configured:
                            console.print("[red]⚠ Warning: Discord bot token not configured in environment variables.[/red]")
                            console.print("[dim]Discord features will not work until DISCORD_BOT_TOKEN is set.[/dim]\n")
                        else:
                            console.print("[green]✓ Discord bot token is configured[/green]\n")
                        
                        console.print("This household doesn't have a Discord channel configured.")
                        console.print("The bot will send group order notifications to this channel.\n")
                        setup_discord = Confirm.ask("Would you like to configure a Discord channel now?", default=True)
                        
                        if setup_discord:
                            console.print("\n[cyan]How to find your Discord channel ID:[/cyan]")
                            console.print("  1. Open Discord → User Settings → Advanced")
                            console.print("  2. Enable 'Developer Mode'")
                            console.print("  3. Right-click on the Discord channel (in your server)")
                            console.print("  4. Click 'Copy ID'\n")
                            
                            discord_channel_id = Prompt.ask("Enter Discord channel ID", default="")
                            if discord_channel_id:
                                household.discord_channel_id = discord_channel_id
                                console.print("[green]✓ Discord channel configured[/green]")
                                
                                if not discord_configured:
                                    console.print("[yellow]⚠ Note: Channel ID saved, but Discord bot token is not configured.[/yellow]")
                                    console.print("[yellow]   The bot will not be able to send messages until DISCORD_BOT_TOKEN is set.[/yellow]\n")
                    
                    await household.save()
                    
                    # Update user's household_id
                    self.current_user.household_id = household.household_id
                    await self.current_user.save()
                    
                    self.current_household = household
                    console.print(f"[green]✓ Joined household: {household.name}[/green]")
                else:
                    console.print("[red]Household not found. Creating new household...[/red]")
                    await self._create_new_household()
            else:
                await self._create_new_household()
        else:
            console.print("[yellow]No existing households found. Let's create a new one.[/yellow]\n")
            await self._create_new_household()
    
    async def _create_new_household(self):
        """Create a new household."""
        name = Prompt.ask("Enter household name (e.g., 'Flat 3B')")
        
        # Discord channel setup
        console.print("\n[bold yellow]Discord Channel Setup[/bold yellow]")
        
        # Check if Discord bot token is configured
        discord_configured = bool(settings.discord_bot_token)
        if not discord_configured:
            console.print("[red]⚠ Warning: Discord bot token not configured in environment variables.[/red]")
            console.print("[dim]Discord features will not work until DISCORD_BOT_TOKEN is set in .env file.[/dim]")
            console.print("[dim]See SETUP.md for instructions on creating a Discord bot.[/dim]\n")
        else:
            console.print("[green]✓ Discord bot token is configured[/green]\n")
        
        console.print("Discord is the preferred messaging channel for group orders and notifications.")
        console.print("The bot will send messages with YES/NO buttons to this channel for group orders.\n")
        
        has_discord = Confirm.ask("Do you have a Discord channel for this household?", default=True)
        
        discord_channel_id = None
        if has_discord:
            console.print("\n[cyan]How to find your Discord channel ID:[/cyan]")
            console.print("  1. Open Discord → User Settings → Advanced")
            console.print("  2. Enable 'Developer Mode'")
            console.print("  3. Right-click on the Discord channel (in your server)")
            console.print("  4. Click 'Copy ID'\n")
            
            discord_channel_id_input = Prompt.ask("Enter Discord channel ID", default="")
            if discord_channel_id_input:
                discord_channel_id = discord_channel_id_input
                console.print("[green]✓ Discord channel configured[/green]")
                
                if not discord_configured:
                    console.print("[yellow]⚠ Note: Channel ID saved, but Discord bot token is not configured.[/yellow]")
                    console.print("[yellow]   The bot will not be able to send messages until DISCORD_BOT_TOKEN is set.[/yellow]\n")
            else:
                console.print("[yellow]⚠ No Discord channel ID provided. You can add it later.[/yellow]")
        else:
            console.print("[yellow]⚠ Discord not configured. You can add it later via household settings.[/yellow]")
            if discord_configured:
                console.print("[dim]Note: Discord bot is configured, but no channel is set for this household.[/dim]\n")
        
        # WhatsApp (optional fallback)
        console.print("\n[yellow]WhatsApp Setup (Optional)[/yellow]")
        has_whatsapp = Confirm.ask("Do you want to configure WhatsApp as a fallback?", default=False)
        whatsapp_group_id = None
        if has_whatsapp:
            whatsapp_group_id = Prompt.ask("Enter WhatsApp group ID/phone (optional)", default="")
        
        household = Household(
            name=name,
            discord_channel_id=discord_channel_id,
            whatsapp_group_id=whatsapp_group_id if whatsapp_group_id else None,
        )
        
        # Add current user as first member
        household.add_member(self.current_user.user_id)
        await household.insert()
        
        # Update user's household_id
        self.current_user.household_id = household.household_id
        await self.current_user.save()
        
        self.current_household = household
        console.print(f"[green]✓ Created household: {household.name}[/green]")
    
    async def _command_loop(self):
        """Main command processing loop."""
        while self.running:
            try:
                # Check for new WhatsApp messages before prompting for input
                await self._check_and_display_new_messages()
                
                # Get user input
                command = Prompt.ask("\n[bold cyan]You[/bold cyan]")
                
                if not command.strip():
                    continue
                
                # Check for exit commands
                if command.lower() in ["exit", "quit", "q"]:
                    self.running = False
                    console.print("[yellow]Goodbye! 👋[/yellow]")
                    break
                
                # Check for help
                if command.lower() == "help":
                    self._display_help()
                    continue
                
                # Process command with agent (always pass user_id)
                console.print("[dim]Processing...[/dim]")
                response = await self.agent.process_command(
                    command,
                    user_id=self.current_user.user_id if self.current_user else None
                )
                
                # Display response
                console.print(f"\n[bold green]Agent:[/bold green] {response}")
                
                # Check if a group order was created and wait for responses
                await self._check_and_wait_for_group_order(response)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit properly.[/yellow]")
                continue
            except Exception as e:
                logger.error(f"Error in command loop: {e}")
                console.print(f"[red]Error: {e}[/red]")
    
    async def _check_and_display_new_messages(self) -> None:
        """
        Check for new WhatsApp messages in the conversation and display them.
        This runs before each command prompt to show messages in real-time.
        """
        try:
            if not self.current_user or not self.agent:
                return
            
            user_id = self.current_user.user_id
            session_id = user_id or "anonymous"
            
            # Initialize tracking for this user if not exists
            if session_id not in self.last_message_count:
                self.last_message_count[session_id] = 0
            if session_id not in self.displayed_messages:
                self.displayed_messages[session_id] = set()
            
            # Check for new messages in conversation
            if hasattr(self.agent, 'conversations') and session_id in self.agent.conversations:
                conversation = self.agent.conversations[session_id]
                current_message_count = len(conversation)
                last_count = self.last_message_count[session_id]
                
                # If we have new messages, display them
                if current_message_count > last_count:
                    new_messages = conversation[last_count:]
                    for msg in new_messages:
                        # Create a unique ID for this message to avoid duplicates
                        msg_content = msg.get('content', '')
                        msg_id = f"{msg.get('role')}_{msg_content[:100]}"
                        
                        if msg_id not in self.displayed_messages[session_id]:
                            self.displayed_messages[session_id].add(msg_id)
                            
                            # Display WhatsApp messages
                            if msg.get('role') == 'user' and 'WhatsApp' in msg_content:
                                console.print(f"\n[bold yellow]📱 WhatsApp:[/bold yellow] {msg_content}")
                            elif msg.get('role') == 'assistant' and 'WhatsApp' in msg_content:
                                console.print(f"\n[bold cyan]📱 System:[/bold cyan] {msg_content}")
                    
                    self.last_message_count[session_id] = current_message_count
                    
        except Exception as e:
            logger.debug(f"Error checking for new messages: {e}")
            # Silently fail - don't interrupt the user experience
    
    async def _check_and_wait_for_group_order(self, response: str) -> None:
        """
        Check if a group order was created and wait for WhatsApp responses.
        
        Checks for any recent group orders created by this user (within the last 60 seconds)
        and automatically enters the wait loop if one is found.
        """
        try:
            if not self.current_user:
                return
            
            # Check for any recent orders created by this user in the last 60 seconds
            # This is more reliable than keyword matching on the text response
            from datetime import timedelta
            recent_time = datetime.utcnow() - timedelta(seconds=60)
            
            recent_orders = await Order.find(
                Order.created_by == self.current_user.user_id,
                Order.timestamp >= recent_time
            ).sort("-timestamp").to_list()
            
            if not recent_orders:
                return
            
            # Find the most recent group order that's still pending and hasn't been processed
            for order in recent_orders:
                if order.order_id in self.processed_orders:
                    continue
                
                # Check if it's a group order that's still pending
                if order.is_group_order and order.status == OrderStatus.PENDING:
                    # Mark as processed
                    self.processed_orders.add(order.order_id)
                    console.print(f"\n[yellow]📱 Group order detected! Order ID: {order.order_id[:8]}...[/yellow]")
                    console.print("[yellow]Waiting for WhatsApp responses (infinite loop - press Ctrl+C to exit)...[/yellow]")
                    await self._wait_for_order_responses(order.order_id, timeout_seconds=0)  # 0 = infinite loop
                    return  # Only process one order at a time
                    
        except Exception as e:
            logger.debug(f"Error checking for group order: {e}")
            # Silently fail - don't interrupt the user experience
    
    async def _wait_for_order_responses(self, order_id: str, timeout_seconds: int = 300) -> None:
        """
        Wait for WhatsApp webhook responses to a group order.
        Polls for new messages in the conversation and displays them in real-time.
        
        Args:
            order_id: Order ID to wait for
            timeout_seconds: Maximum time to wait (default: 5 minutes, 0 = infinite)
        """
        start_time = datetime.utcnow()
        poll_interval = 2  # Poll every 2 seconds
        last_status = None
        last_message_count = 0
        displayed_messages = set()  # Track which messages we've already displayed
        
        if not self.current_user:
            return
        
        user_id = self.current_user.user_id
        session_id = user_id or "anonymous"
        
        # Get initial conversation length
        if hasattr(self.agent, 'conversations') and session_id in self.agent.conversations:
            initial_conversation = self.agent.conversations[session_id]
            last_message_count = len(initial_conversation)
        
        with Live(self._create_status_display("Waiting for WhatsApp responses..."), refresh_per_second=2) as live:
            try:
                while True:
                    try:
                        # Check for new messages in conversation
                        if hasattr(self.agent, 'conversations') and session_id in self.agent.conversations:
                            conversation = self.agent.conversations[session_id]
                            current_message_count = len(conversation)
                            
                            # If we have new messages, display them
                            if current_message_count > last_message_count:
                                new_messages = conversation[last_message_count:]
                                for msg in new_messages:
                                    # Create a unique ID for this message to avoid duplicates
                                    msg_id = f"{msg.get('role')}_{msg.get('content', '')[:50]}"
                                    if msg_id not in displayed_messages:
                                        displayed_messages.add(msg_id)
                                        
                                        # Display WhatsApp messages
                                        if msg.get('role') == 'user' and 'WhatsApp' in msg.get('content', ''):
                                            console.print(f"\n[bold yellow]📱 WhatsApp:[/bold yellow] {msg.get('content', '')}")
                                        elif msg.get('role') == 'assistant' and 'WhatsApp' in msg.get('content', ''):
                                            console.print(f"\n[bold cyan]📱 System:[/bold cyan] {msg.get('content', '')}")
                                
                                last_message_count = current_message_count
                        
                        # Poll the order status via API
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            response = await client.get(
                                f"{self.api_base_url}/orders/{order_id}"
                            )
                            
                            if response.status_code == 200:
                                order_data = response.json()
                                current_status = order_data.get("status")
                                
                                # Update display if status changed
                                if current_status != last_status:
                                    last_status = current_status
                                    
                                    # Check if order is finalized
                                    if current_status in [OrderStatus.CONFIRMED.value, OrderStatus.CANCELLED.value]:
                                        elapsed = (datetime.utcnow() - start_time).total_seconds()
                                        live.update(self._create_status_display(
                                            f"✅ Order finalized! Status: {current_status}",
                                            elapsed=elapsed
                                        ))
                                        await asyncio.sleep(1)
                                        return
                                    
                                    # Update display with current status
                                    pending_count = sum(
                                        len(users) for users in 
                                        order_data.get("pending_responses", {}).values()
                                    )
                                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                                    
                                    live.update(self._create_status_display(
                                        f"Status: {current_status} | Pending: {pending_count} users",
                                        elapsed=elapsed
                                    ))
                            else:
                                logger.warning(f"Failed to fetch order status: {response.status_code}")
                            
                    except httpx.RequestError as e:
                        logger.debug(f"Error polling order status: {e}")
                        # Continue polling even if one request fails
                    except Exception as e:
                        logger.debug(f"Error in wait loop: {e}")
                        # Continue polling
                    
                    # Check timeout (only if timeout_seconds > 0, otherwise infinite loop)
                    if timeout_seconds > 0:
                        elapsed = (datetime.utcnow() - start_time).total_seconds()
                        if elapsed >= timeout_seconds:
                            live.update(self._create_status_display(
                                f"⏱️ Timeout reached ({timeout_seconds}s). Order may still be pending.",
                                elapsed=elapsed
                            ))
                            await asyncio.sleep(1)
                            return
                    
                    await asyncio.sleep(poll_interval)
            except KeyboardInterrupt:
                console.print("\n[yellow]Exiting wait loop. You can continue with other commands.[/yellow]")
                return
    
    def _create_status_display(self, message: str, elapsed: float = 0) -> Text:
        """Create a status display text for the live update."""
        elapsed_str = f"{int(elapsed)}s" if elapsed > 0 else ""
        status_text = Text()
        status_text.append("📱 ", style="yellow")
        status_text.append(message, style="cyan")
        if elapsed_str:
            status_text.append(f" ({elapsed_str})", style="dim")
        return status_text
    
    def _display_help(self):
        """Display help information."""
        help_text = """
**Example Commands:**

**Ordering:**
- "Order 2 liters of milk"
- "Buy 12 eggs and 1kg of cheese"
- "Purchase bread and butter"

**Inventory Management:**
- "What's in the inventory?"
- "Show all items"
- "Add 3 apples to inventory"
- "Show low stock items"

**Orders:**
- "Show recent orders"
- "What's the status of my order?"

**System:**
- "help" - Show this help message
- "exit" or "quit" - Exit the application
        """
        console.print(Panel(Markdown(help_text), title="Help", border_style="blue"))
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.agent:
            logger.info("Shutting down agent")
        await db.close()


async def main():
    """Main entry point for the CLI."""
    cli = GroceryCLI()
    
    try:
        await cli.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        logger.exception("Fatal error in CLI")
    finally:
        await cli.cleanup()


if __name__ == "__main__":
    # Configure logger
    logger.add(
        "logs/grocery_agent_{time}.log",
        rotation="1 day",
        retention="7 days",
        level=settings.log_level,
    )
    
    # Run CLI
    asyncio.run(main())

