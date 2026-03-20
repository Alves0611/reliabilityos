from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import messaging
from app.routers import health, orders, products


@asynccontextmanager
async def lifespan(app: FastAPI):
    await messaging.connect()
    yield
    await messaging.disconnect()


app = FastAPI(title="Orders API", version="0.1.0", lifespan=lifespan)

app.include_router(products.router)
app.include_router(orders.router)
app.include_router(health.router)
