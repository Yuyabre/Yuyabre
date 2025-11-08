"""
Router for order-related endpoints.
"""
from fastapi import APIRouter
from typing import List

from api.controllers.orders_controller import OrdersController
from models import Order

router = APIRouter(prefix="/orders", tags=["Orders"])

controller = OrdersController()


@router.get("", response_model=List[Order])
async def get_orders(limit: int = 20):
    """Get recent order history."""
    return await controller.get_order_history(limit)


@router.get("/{order_id}", response_model=Order)
async def get_order(order_id: str):
    """Get a specific order by ID."""
    return await controller.get_order_by_id(order_id)


@router.post("/{order_id}/cancel")
async def cancel_order(order_id: str):
    """Cancel an order."""
    return await controller.cancel_order(order_id)

