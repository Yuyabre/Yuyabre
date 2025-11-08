"""
Inventory Management Module

Handles all inventory-related operations including CRUD, low-stock detection,
and expiration tracking.
"""
from .service import InventoryService

__all__ = ["InventoryService"]

