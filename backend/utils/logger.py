"""
Logging configuration and utilities.
"""
import sys
from loguru import logger
from config import settings


def setup_logger():
    """
    Configure the application logger.
    """
    # Remove default logger
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # Add file handler
    logger.add(
        "logs/app_{time}.log",
        rotation="1 day",
        retention="7 days",
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
    
    logger.info("Logger configured")

