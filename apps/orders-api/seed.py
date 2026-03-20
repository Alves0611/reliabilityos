import asyncio
import logging
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)

PRODUCTS = [
    {"name": "Widget Pro", "price": Decimal("29.99"), "stock": 100, "description": "A reliable widget"},
    {"name": "Gadget Ultra", "price": Decimal("49.99"), "stock": 50, "description": "An ultra gadget"},
    {"name": "Connector Basic", "price": Decimal("9.99"), "stock": 200, "description": "A basic connector"},
    {"name": "Sensor Max", "price": Decimal("79.99"), "stock": 30, "description": "A max sensor"},
    {"name": "Module Core", "price": Decimal("19.99"), "stock": 150, "description": "A core module"},
]


async def seed():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        for product in PRODUCTS:
            await conn.execute(
                text(
                    """
                    INSERT INTO products (id, name, description, price, stock)
                    VALUES (gen_random_uuid(), :name, :description, :price, :stock)
                    ON CONFLICT (name) DO NOTHING
                    """
                ),
                product,
            )
    await engine.dispose()
    logger.info("Seed completed: %d products", len(PRODUCTS))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
