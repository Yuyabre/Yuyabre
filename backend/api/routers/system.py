"""
Router for system-related endpoints (health checks, etc.).
"""
from fastapi import APIRouter

from api.controllers.system_controller import SystemController

router = APIRouter(tags=["System"])

controller = SystemController()


@router.get("/health")
async def health_check():
    """Check API and database health."""
    return await controller.health_check()

