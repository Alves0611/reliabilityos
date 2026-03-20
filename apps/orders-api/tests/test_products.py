import pytest


@pytest.mark.asyncio
async def test_list_products_empty(client):
    response = await client.get("/products")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_products(client, seed_products):
    response = await client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = {p["name"] for p in data}
    assert names == {"Widget Pro", "Gadget Ultra"}


@pytest.mark.asyncio
async def test_get_product_by_id(client, seed_products):
    product = seed_products[0]
    response = await client.get(f"/products/{product.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Widget Pro"
    assert data["price"] == "29.99"


@pytest.mark.asyncio
async def test_get_product_not_found(client):
    import uuid

    response = await client.get(f"/products/{uuid.uuid4()}")
    assert response.status_code == 404
