"""
Router for Splitwise-related endpoints.
"""
from fastapi import APIRouter, Query, Body

from api.controllers.splitwise_controller import SplitwiseController
from api.serializers import SearchGroupsRequest, CreateExpenseRequest

router = APIRouter(prefix="/splitwise", tags=["Splitwise"])

controller = SplitwiseController()


@router.get("/expenses")
async def get_splitwise_expenses(
    user_id: str = Query(..., description="Internal user ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of expenses to retrieve")
):
    """Get recent Splitwise expenses for a user."""
    return await controller.get_expenses(user_id, limit)


@router.post("/groups/search")
async def search_groups(
    user_id: str = Query(..., description="Internal user ID"),
    request: SearchGroupsRequest = Body(..., description="Search query for group name")
):
    """
    Search for Splitwise groups by name.
    
    Returns groups that match the search query (case-insensitive partial match).
    """
    return await controller.search_groups(user_id, request.query)


@router.post("/expenses")
async def create_expense(
    user_id: str = Query(..., description="Internal user ID"),
    request: CreateExpenseRequest = Body(..., description="Expense details")
):
    """
    Create a new expense in Splitwise.
    
    This endpoint can be called by the agent to create expenses with specified splits,
    users involved, and items purchased.
    """
    return await controller.create_expense(
        user_id=user_id,
        description=request.description,
        amount=request.amount,
        splitwise_user_ids=request.splitwise_user_ids,
        group_id=request.group_id,
        category=request.category,
        date=request.date,
        notes=request.notes,
        split_method=request.split_method,
        paid_by_user_id=request.paid_by_user_id,
    )

