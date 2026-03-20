from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import messaging
from app.logging_config import setup_logging
from app.middleware import MetricsMiddleware
from app.routers import health, orders, products
from app.telemetry import setup_telemetry

# Initialize observability before anything else
setup_telemetry()
setup_logging()

# Auto-instrument after provider is set
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from app.database import engine

SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await messaging.connect()
    yield
    await messaging.disconnect()


app = FastAPI(title="Orders API", version="0.1.0", lifespan=lifespan)

app.add_middleware(MetricsMiddleware)

FastAPIInstrumentor.instrument_app(app)

app.include_router(products.router)
app.include_router(orders.router)
app.include_router(health.router)

static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
