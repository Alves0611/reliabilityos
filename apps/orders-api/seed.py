import asyncio
import logging
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)

PRODUCTS = [
    {"name": "Banana Orgânica", "price": Decimal("2.49"), "stock": 120, "description": "Cacho com 6 unidades, importada do Equador"},
    {"name": "Ovos Caipira", "price": Decimal("5.99"), "stock": 80, "description": "Dúzia de ovos grandes, galinhas livres"},
    {"name": "Abacate Hass", "price": Decimal("1.89"), "stock": 200, "description": "Maduro e pronto pra consumo"},
    {"name": "Pão de Fermentação Natural", "price": Decimal("6.50"), "stock": 40, "description": "Artesanal, assado na hora"},
    {"name": "Iogurte Grego", "price": Decimal("4.29"), "stock": 150, "description": "500g, natural, alto teor proteico"},
    {"name": "Salmão Atlântico", "price": Decimal("12.99"), "stock": 30, "description": "Filé fresco, porção de 300g"},
    {"name": "Tomate Cereja", "price": Decimal("3.49"), "stock": 90, "description": "Bandeja 250g, amadurecido no pé"},
    {"name": "Leite de Aveia", "price": Decimal("3.99"), "stock": 100, "description": "1L, edição barista"},
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
