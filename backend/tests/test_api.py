"""
Tests for FastAPI endpoints.
"""
import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    
    assert response.status_code == 200
    assert "status" in response.json()


@pytest.mark.asyncio
async def test_get_inventory():
    """Test getting inventory list."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/inventory")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_process_command():
    """Test agent command processing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/agent/command",
            json={"command": "Show inventory"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "message" in data

