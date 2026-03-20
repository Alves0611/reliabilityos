from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_health_all_up(client):
    with patch("app.routers.health.messaging.is_healthy", new_callable=AsyncMock, return_value=True):
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "up"
    assert data["rabbitmq"] == "up"


@pytest.mark.asyncio
async def test_health_rabbitmq_down(client):
    with patch("app.routers.health.messaging.is_healthy", new_callable=AsyncMock, return_value=False):
        response = await client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["rabbitmq"] == "down"


@pytest.mark.asyncio
async def test_ready(client):
    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_metrics_placeholder(client):
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "placeholder" in response.text
