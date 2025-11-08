"""
Router for Splitwise-related endpoints.
"""
from fastapi import APIRouter

from api.controllers.splitwise_controller import SplitwiseController

router = APIRouter(prefix="/splitwise", tags=["Splitwise"])

controller = SplitwiseController()


@router.get("/expenses")
async def get_splitwise_expenses(limit: int = 20):
    """Get recent Splitwise expenses."""
    return await controller.get_expenses(limit)

