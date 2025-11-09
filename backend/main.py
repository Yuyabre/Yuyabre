"""
FastAPI Application - REST API for the Grocery Management Agent.

Provides HTTP endpoints for web/mobile interfaces to interact with the agent.
"""
from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from database import db
from config import settings
from api.routers import agent, inventory, orders, splitwise, splitwise_auth, system, whatsapp, discord, user
from api.websocket_manager import websocket_manager
from api.dependencies import discord_service


# Lifespan event handler for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.
    
    Handles database connection on startup and cleanup on shutdown.
    """
    # Startup
    logger.info("Starting Grocery Management Agent API")
    await db.connect()
    
    # Start Discord bot in background if configured
    # Use shared instance from dependencies
    discord_task = None
    if discord_service.is_configured():
        logger.info("Discord service is configured, starting bot in background task...")
        async def run_discord_bot():
            try:
                logger.info("Background task: Starting Discord bot...")
                await discord_service.start_bot()
                logger.info("Background task: Discord bot.start() completed")
            except Exception as e:
                logger.error(f"Background task: Discord bot error: {e}", exc_info=True)
        
        discord_task = asyncio.create_task(run_discord_bot())
        logger.info("Discord bot background task created and started")
    else:
        logger.warning("Discord service not configured - bot will not start")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Grocery Management Agent API")
    
    # Stop Discord bot
    if discord_task:
        await discord_service.stop_bot()
        discord_task.cancel()
        try:
            await discord_task
        except asyncio.CancelledError:
            pass
        logger.info("Discord bot stopped")
    
    # Close all WebSocket connections
    await websocket_manager.close_all_connections()
    await db.close()


# Create FastAPI app
app = FastAPI(
    title="Grocery Management Agent API",
    description="REST API for shared flat grocery management and automation",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(system.router)
app.include_router(user.router)
app.include_router(agent.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(splitwise.router)
app.include_router(splitwise_auth.router)
app.include_router(whatsapp.router)
app.include_router(discord.router)


if __name__ == "__main__":
    import uvicorn
    
    logger.add(
        "logs/api_{time}.log",
        rotation="1 day",
        retention="7 days",
        level=settings.log_level,
    )
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
    )

