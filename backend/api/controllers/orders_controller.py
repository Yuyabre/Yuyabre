"""
Controller for order-related operations.
"""
from fastapi import HTTPException, status
from typing import List

from api.dependencies import ordering_service
from models import Order


class OrdersController:
    """Controller for handling order operations."""
    
    @staticmethod
    async def get_order_history(limit: int = 20) -> List[Order]:
        """Get recent order history."""
        return await ordering_service.get_order_history(limit)
    
    @staticmethod
    async def get_order_by_id(order_id: str) -> Order:
        """
        Get a specific order by ID.
        
        Raises:
            HTTPException: If order not found
        """
        order = await Order.find_one(Order.order_id == order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        return order
    
    @staticmethod
    async def cancel_order(order_id: str) -> dict:
        """
        Cancel an order.
        
        Raises:
            HTTPException: If order cannot be cancelled
        """
        success = await ordering_service.cancel_order(order_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel order"
            )
        return {"message": "Order cancelled successfully"}

