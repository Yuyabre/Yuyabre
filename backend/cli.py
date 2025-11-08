"""
Command-Line Interface for the Grocery Management Agent.

Provides a text-based interface for interacting with the agent.
"""
import asyncio
from loguru import logger
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown

from database import db
from agent.core import GroceryAgent
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
    
    async def start(self):
        """Start the CLI interface."""
        # Display welcome banner
        self._display_welcome()
        
        # Connect to database
        await self._setup_database()
        
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
    
    async def _command_loop(self):
        """Main command processing loop."""
        while self.running:
            try:
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
                
                # Process command with agent
                console.print("[dim]Processing...[/dim]")
                response = await self.agent.process_command(command)
                
                # Display response
                console.print(f"\n[bold green]Agent:[/bold green] {response}")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit properly.[/yellow]")
                continue
            except Exception as e:
                logger.error(f"Error in command loop: {e}")
                console.print(f"[red]Error: {e}[/red]")
    
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

