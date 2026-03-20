import uuid
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_create_order(client, seed_products):
    product = seed_products[0]
    with patch("app.routers.orders.messaging.publish_task", new_callable=AsyncMock) as mock_pub:
        response = await client.post(
            "/orders",
            json={"items": [{"product_id": str(product.id), "quantity": 2}]},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["total"] == "59.98"
    assert len(data["items"]) == 1
    mock_pub.assert_called_once()


@pytest.mark.asyncio
async def test_create_order_insufficient_stock(client, seed_products):
    product = seed_products[0]
    response = await client.post(
        "/orders",
        json={"items": [{"product_id": str(product.id), "quantity": 999}]},
    )
    assert response.status_code == 400
    assert "insufficient stock" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_order_product_not_found(client):
    response = await client.post(
        "/orders",
        json={"items": [{"product_id": str(uuid.uuid4()), "quantity": 1}]},
    )
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_order_empty_items(client):
    response = await client.post("/orders", json={"items": []})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_order_invalid_quantity(client, seed_products):
    product = seed_products[0]
    response = await client.post(
        "/orders",
        json={"items": [{"product_id": str(product.id), "quantity": 0}]},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_orders(client, seed_products):
    product = seed_products[0]
    with patch("app.routers.orders.messaging.publish_task", new_callable=AsyncMock):
        await client.post(
            "/orders",
            json={"items": [{"product_id": str(product.id), "quantity": 1}]},
        )

    response = await client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_get_order_by_id(client, seed_products):
    product = seed_products[0]
    with patch("app.routers.orders.messaging.publish_task", new_callable=AsyncMock):
        create_resp = await client.post(
            "/orders",
            json={"items": [{"product_id": str(product.id), "quantity": 1}]},
        )

    order_id = create_resp.json()["id"]
    response = await client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order_id
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_order_not_found(client):
    response = await client.get(f"/orders/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_order_decrements_stock(client, seed_products):
    product = seed_products[0]
    with patch("app.routers.orders.messaging.publish_task", new_callable=AsyncMock):
        await client.post(
            "/orders",
            json={"items": [{"product_id": str(product.id), "quantity": 10}]},
        )

    response = await client.get(f"/products/{product.id}")
    assert response.json()["stock"] == 90


@pytest.mark.asyncio
async def test_create_order_multiple_items(client, seed_products):
    p1, p2 = seed_products
    with patch("app.routers.orders.messaging.publish_task", new_callable=AsyncMock):
        response = await client.post(
            "/orders",
            json={
                "items": [
                    {"product_id": str(p1.id), "quantity": 1},
                    {"product_id": str(p2.id), "quantity": 2},
                ]
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == "129.97"


@pytest.mark.asyncio
async def test_list_orders_ordered_by_created_at_desc(client, seed_products):
    product = seed_products[0]
    with patch("app.routers.orders.messaging.publish_task", new_callable=AsyncMock):
        resp1 = await client.post(
            "/orders",
            json={"items": [{"product_id": str(product.id), "quantity": 1}]},
        )
        resp2 = await client.post(
            "/orders",
            json={"items": [{"product_id": str(product.id), "quantity": 2}]},
        )

    response = await client.get("/orders")
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == resp2.json()["id"]
    assert data[1]["id"] == resp1.json()["id"]
