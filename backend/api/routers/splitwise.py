"""
Router for Splitwise-related endpoints.
"""
from fastapi import APIRouter, Query

from api.controllers.splitwise_controller import SplitwiseController

router = APIRouter(prefix="/splitwise", tags=["Splitwise"])

controller = SplitwiseController()


@router.get("/expenses")
async def get_splitwise_expenses(
    user_id: str = Query(..., description="Internal user ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of expenses to retrieve")
):
    """Get recent Splitwise expenses for a user."""
    return await controller.get_expenses(user_id, limit)

