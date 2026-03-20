# Phase 1 — Application Core Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a working FastAPI orders API + Celery worker with PostgreSQL, RabbitMQ, and Redis, all running via Docker Compose.

**Architecture:** FastAPI async API publishes order events to RabbitMQ via aio-pika. Celery worker consumes events, processes orders (status machine), and publishes completion events. PostgreSQL stores data (async in API, sync in worker). Redis is Celery's result backend.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async+sync), Alembic, Celery 5.x, aio-pika, PostgreSQL 16, RabbitMQ 3.13, Redis 7, pytest, TestContainers, Docker Compose.

**Spec:** `docs/superpowers/specs/application-core.md`

---

## File Map

```
apps/
├── orders-api/
│   ├── app/
│   │   ├── __init__.py              # empty
│   │   ├── main.py                  # FastAPI app, lifespan, router mounts
│   │   ├── config.py                # Settings via pydantic-settings
│   │   ├── database.py              # async engine + async session factory
│   │   ├── models.py                # Product, Order, OrderItem (SQLAlchemy)
│   │   ├── schemas.py               # Pydantic request/response models
│   │   ├── messaging.py             # RabbitMQ publisher via aio-pika
│   │   └── routers/
│   │       ├── __init__.py          # empty
│   │       ├── products.py          # GET /products, GET /products/{id}
│   │       ├── orders.py            # POST /orders, GET /orders, GET /orders/{id}
│   │       └── health.py            # GET /health, GET /ready, GET /metrics
│   ├── alembic.ini                  # Alembic config
│   ├── alembic/
│   │   ├── env.py                   # Alembic env with async support
│   │   ├── script.py.mako           # Migration template
│   │   └── versions/
│   │       └── 001_initial.py       # Initial migration
│   ├── tests/
│   │   ├── __init__.py              # empty
│   │   ├── conftest.py              # fixtures, async test client, mock deps
│   │   ├── test_products.py         # unit tests for products endpoints
│   │   ├── test_orders.py           # unit tests for orders endpoints
│   │   ├── test_health.py           # unit tests for health endpoints
│   │   └── test_integration.py      # TestContainers full-flow tests
│   ├── seed.py                      # Idempotent product seeder
│   ├── entrypoint.sh                # alembic upgrade + seed + uvicorn
│   ├── .dockerignore                # Exclude tests, cache, git from image
│   ├── Dockerfile                   # Multi-stage Python image
│   └── pyproject.toml               # Dependencies + pytest config
├── worker/
│   ├── worker/
│   │   ├── __init__.py              # empty
│   │   ├── celery_app.py            # Celery app + queue config
│   │   ├── config.py                # Settings via pydantic-settings
│   │   ├── database.py              # sync engine + session factory
│   │   ├── models.py                # Same models as API (sync base)
│   │   └── tasks.py                 # process_order task
│   ├── tests/
│   │   ├── __init__.py              # empty
│   │   ├── conftest.py              # fixtures, mock DB
│   │   └── test_tasks.py            # unit tests for process_order
│   ├── .dockerignore                # Exclude tests, cache, git from image
│   ├── Dockerfile                   # Multi-stage Python image
│   └── pyproject.toml               # Dependencies + pytest config
docker-compose.yml                   # All services
```

---

## Chunk 1: Project Scaffolding + Data Layer

### Task 1: Orders API Project Setup

**Files:**
- Create: `apps/orders-api/pyproject.toml`
- Create: `apps/orders-api/app/__init__.py`
- Create: `apps/orders-api/app/routers/__init__.py`
- Create: `apps/orders-api/tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "orders-api"
version = "0.1.0"
description = "ReliabilityOS Orders API"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pydantic-settings>=2.7.0",
    "aio-pika>=9.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.25.0",
    "httpx>=0.28.0",
    "aiosqlite>=0.20.0",
    "testcontainers[postgres,rabbitmq,redis]>=4.9.0",
    "psycopg2-binary>=2.9.0",
]

[tool.setuptools.packages.find]
include = ["app*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create empty __init__.py files**

Create empty files at:
- `apps/orders-api/app/__init__.py`
- `apps/orders-api/app/routers/__init__.py`
- `apps/orders-api/tests/__init__.py`

- [ ] **Step 3: Commit**

```bash
git add apps/orders-api/pyproject.toml apps/orders-api/app/__init__.py apps/orders-api/app/routers/__init__.py apps/orders-api/tests/__init__.py
git commit -m "feat(api): scaffold orders-api project structure"
```

---

### Task 2: Worker Project Setup

**Files:**
- Create: `apps/worker/pyproject.toml`
- Create: `apps/worker/worker/__init__.py`
- Create: `apps/worker/tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "worker"
version = "0.1.0"
description = "ReliabilityOS Order Processing Worker"
requires-python = ">=3.12"
dependencies = [
    "celery[redis]>=5.4.0",
    "sqlalchemy>=2.0.36",
    "psycopg2-binary>=2.9.0",
    "pydantic-settings>=2.7.0",
    "pika>=1.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
]

[tool.setuptools.packages.find]
include = ["worker*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create empty __init__.py files**

Create empty files at:
- `apps/worker/worker/__init__.py`
- `apps/worker/tests/__init__.py`

- [ ] **Step 3: Commit**

```bash
git add apps/worker/
git commit -m "feat(worker): scaffold worker project structure"
```

---

### Task 3: Configuration (Both Apps)

**Files:**
- Create: `apps/orders-api/app/config.py`
- Create: `apps/worker/worker/config.py`

- [ ] **Step 1: Create API config**

```python
# apps/orders-api/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/orders"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672//"
    app_name: str = "orders-api"

    model_config = {"env_prefix": "ORDERS_"}


settings = Settings()
```

- [ ] **Step 2: Create Worker config**

```python
# apps/worker/worker/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/orders"
    broker_url: str = "amqp://guest:guest@rabbitmq:5672//"
    result_backend: str = "redis://redis:6379/0"

    model_config = {"env_prefix": "WORKER_"}


settings = Settings()
```

- [ ] **Step 3: Commit**

```bash
git add apps/orders-api/app/config.py apps/worker/worker/config.py
git commit -m "feat: add pydantic-settings config for api and worker"
```

---

### Task 4: SQLAlchemy Models

**Files:**
- Create: `apps/orders-api/app/models.py`
- Create: `apps/worker/worker/models.py`

- [ ] **Step 1: Create API models (async base)**

```python
# apps/orders-api/app/models.py
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
```

- [ ] **Step 2: Create Worker models (sync base, same schema)**

```python
# apps/worker/worker/models.py
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
```

- [ ] **Step 3: Commit**

```bash
git add apps/orders-api/app/models.py apps/worker/worker/models.py
git commit -m "feat: add SQLAlchemy models for Product, Order, OrderItem"
```

---

### Task 5: Database Layer

**Files:**
- Create: `apps/orders-api/app/database.py`
- Create: `apps/worker/worker/database.py`

- [ ] **Step 1: Create async database layer (API)**

```python
# apps/orders-api/app/database.py
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

- [ ] **Step 2: Create sync database layer (Worker)**

```python
# apps/worker/worker/database.py
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from worker.config import settings

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: Commit**

```bash
git add apps/orders-api/app/database.py apps/worker/worker/database.py
git commit -m "feat: add async and sync database session factories"
```

---

### Task 6: Alembic Setup + Initial Migration

**Files:**
- Create: `apps/orders-api/alembic.ini`
- Create: `apps/orders-api/alembic/env.py`
- Create: `apps/orders-api/alembic/script.py.mako`
- Create: `apps/orders-api/alembic/versions/001_initial.py`

- [ ] **Step 1: Create alembic.ini**

```ini
# apps/orders-api/alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@postgres:5432/orders

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: Create alembic/env.py with async support**

```python
# apps/orders-api/alembic/env.py
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

- [ ] **Step 3: Create script.py.mako**

```mako
# apps/orders-api/alembic/script.py.mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 4: Create initial migration**

```python
# apps/orders-api/alembic/versions/001_initial.py
"""initial tables

Revision ID: 001
Revises:
Create Date: 2026-03-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "order_id",
            sa.Uuid(),
            sa.ForeignKey("orders.id"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Uuid(),
            sa.ForeignKey("products.id"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("products")
```

- [ ] **Step 5: Commit**

```bash
git add apps/orders-api/alembic.ini apps/orders-api/alembic/
git commit -m "feat(api): add Alembic setup with initial migration"
```

---

### Task 7: Pydantic Schemas

**Files:**
- Create: `apps/orders-api/app/schemas.py`

- [ ] **Step 1: Create schemas**

```python
# apps/orders-api/app/schemas.py
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    price: Decimal
    stock: int
    created_at: datetime


class OrderItemRequest(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    items: list[OrderItemRequest] = Field(min_length=1)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    total: Decimal
    created_at: datetime
    updated_at: datetime


class OrderDetailResponse(OrderResponse):
    items: list[OrderItemResponse]


class HealthResponse(BaseModel):
    status: str
    database: str
    rabbitmq: str
```

- [ ] **Step 2: Commit**

```bash
git add apps/orders-api/app/schemas.py
git commit -m "feat(api): add Pydantic request/response schemas"
```

---

## Chunk 2: API Routers + Messaging

### Task 8: RabbitMQ Messaging Layer

**Files:**
- Create: `apps/orders-api/app/messaging.py`

- [ ] **Step 1: Create aio-pika publisher**

```python
# apps/orders-api/app/messaging.py
import json
import logging

import aio_pika

from app.config import settings

logger = logging.getLogger(__name__)

_connection: aio_pika.abc.AbstractRobustConnection | None = None
_channel: aio_pika.abc.AbstractChannel | None = None
_orders_exchange: aio_pika.abc.AbstractExchange | None = None


async def connect() -> None:
    global _connection, _channel, _orders_exchange
    _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    _channel = await _connection.channel()

    # Declare exchanges
    orders_exchange = await _channel.declare_exchange(
        "orders", aio_pika.ExchangeType.DIRECT, durable=True
    )
    dlx_exchange = await _channel.declare_exchange(
        "orders.dlx", aio_pika.ExchangeType.DIRECT, durable=True
    )

    # Declare DLQ
    dlq = await _channel.declare_queue("order.created.dlq", durable=True)
    await dlq.bind(dlx_exchange, routing_key="order.created")

    # Declare main queue with DLX
    queue = await _channel.declare_queue(
        "order.created",
        durable=True,
        arguments={
            "x-dead-letter-exchange": "orders.dlx",
            "x-dead-letter-routing-key": "order.created",
        },
    )
    await queue.bind(orders_exchange, routing_key="order.created")

    # Declare completed queue (no consumer in Phase 1)
    completed_queue = await _channel.declare_queue(
        "order.completed",
        durable=True,
        arguments={"x-message-ttl": 86400000},  # 24h TTL
    )
    await completed_queue.bind(orders_exchange, routing_key="order.completed")

    _orders_exchange = orders_exchange
    logger.info("RabbitMQ connected and topology declared")


async def disconnect() -> None:
    global _connection, _channel, _orders_exchange
    if _connection and not _connection.is_closed:
        await _connection.close()
    _connection = None
    _channel = None
    _orders_exchange = None


async def publish(routing_key: str, body: dict) -> None:
    if _orders_exchange is None:
        raise RuntimeError("RabbitMQ not connected")

    message = aio_pika.Message(
        body=json.dumps(body).encode(),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await _orders_exchange.publish(message, routing_key=routing_key)
    logger.info("Published %s: %s", routing_key, body)


async def is_healthy() -> bool:
    return _connection is not None and not _connection.is_closed
```

- [ ] **Step 2: Commit**

```bash
git add apps/orders-api/app/messaging.py
git commit -m "feat(api): add aio-pika RabbitMQ messaging layer"
```

---

### Task 9: Products Router

**Files:**
- Create: `apps/orders-api/app/routers/products.py`
- Create: `apps/orders-api/tests/conftest.py`
- Create: `apps/orders-api/tests/test_products.py`

- [ ] **Step 1: Write tests for products endpoints**

```python
# apps/orders-api/tests/conftest.py
import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.models import Base, Product


@pytest.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.messaging.connect", new_callable=AsyncMock):
        with patch("app.messaging.disconnect", new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def seed_products(db_session) -> list[Product]:
    products = [
        Product(
            id=uuid.uuid4(),
            name="Widget Pro",
            price=Decimal("29.99"),
            stock=100,
            description="A reliable widget",
        ),
        Product(
            id=uuid.uuid4(),
            name="Gadget Ultra",
            price=Decimal("49.99"),
            stock=50,
            description="An ultra gadget",
        ),
    ]
    db_session.add_all(products)
    await db_session.commit()
    for p in products:
        await db_session.refresh(p)
    return products
```

```python
# apps/orders-api/tests/test_products.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/orders-api && pip install -e ".[dev]" && pytest tests/test_products.py -v`
Expected: FAIL (routers/products.py does not exist, main.py does not exist)

- [ ] **Step 3: Implement products router**

```python
# apps/orders-api/app/routers/products.py
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Product
from app.schemas import ProductResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductResponse])
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).order_by(Product.name))
    return result.scalars().all()


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
```

- [ ] **Step 4: Create router stubs (orders + health)**

These stubs are needed so main.py can import all routers. They'll be replaced in Tasks 10 and 11.

```python
# apps/orders-api/app/routers/orders.py (stub)
from fastapi import APIRouter

router = APIRouter()
```

```python
# apps/orders-api/app/routers/health.py (stub)
from fastapi import APIRouter

router = APIRouter()
```

- [ ] **Step 5: Create main.py**

```python
# apps/orders-api/app/main.py
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
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd apps/orders-api && pytest tests/test_products.py -v`
Expected: 4 tests PASS

- [ ] **Step 7: Commit**

```bash
git add apps/orders-api/app/main.py apps/orders-api/app/routers/ apps/orders-api/tests/
git commit -m "feat(api): add products endpoints with tests"
```

---

### Task 10: Orders Router

**Files:**
- Modify: `apps/orders-api/app/routers/orders.py`
- Create: `apps/orders-api/tests/test_orders.py`

- [ ] **Step 1: Write tests for orders endpoints**

```python
# apps/orders-api/tests/test_orders.py
import uuid
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_create_order(client, seed_products):
    product = seed_products[0]
    with patch("app.routers.orders.messaging.publish", new_callable=AsyncMock) as mock_pub:
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
    product = seed_products[0]  # stock=100
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
    with patch("app.routers.orders.messaging.publish", new_callable=AsyncMock):
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
    with patch("app.routers.orders.messaging.publish", new_callable=AsyncMock):
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
    product = seed_products[0]  # stock=100
    with patch("app.routers.orders.messaging.publish", new_callable=AsyncMock):
        await client.post(
            "/orders",
            json={"items": [{"product_id": str(product.id), "quantity": 10}]},
        )

    response = await client.get(f"/products/{product.id}")
    assert response.json()["stock"] == 90


@pytest.mark.asyncio
async def test_create_order_multiple_items(client, seed_products):
    p1, p2 = seed_products  # 29.99 and 49.99
    with patch("app.routers.orders.messaging.publish", new_callable=AsyncMock):
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
    # 29.99 * 1 + 49.99 * 2 = 129.97
    assert data["total"] == "129.97"


@pytest.mark.asyncio
async def test_list_orders_ordered_by_created_at_desc(client, seed_products):
    product = seed_products[0]
    with patch("app.routers.orders.messaging.publish", new_callable=AsyncMock):
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
    # Most recent first
    assert data[0]["id"] == resp2.json()["id"]
    assert data[1]["id"] == resp1.json()["id"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/orders-api && pytest tests/test_orders.py -v`
Expected: FAIL (orders router is a stub)

- [ ] **Step 3: Implement orders router**

```python
# apps/orders-api/app/routers/orders.py
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import messaging
from app.database import get_db
from app.models import Order, OrderItem, Product
from app.schemas import (
    CreateOrderRequest,
    OrderDetailResponse,
    OrderResponse,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: CreateOrderRequest, db: AsyncSession = Depends(get_db)
):
    order_items = []
    total = Decimal("0")

    for item in payload.items:
        result = await db.execute(
            select(Product).where(Product.id == item.product_id)
        )
        product = result.scalar_one_or_none()
        if product is None:
            raise HTTPException(
                status_code=400,
                detail=f"Product {item.product_id} not found",
            )
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. "
                f"Available: {product.stock}, requested: {item.quantity}",
            )

        product.stock -= item.quantity
        line_total = product.price * item.quantity
        total += line_total

        order_items.append(
            OrderItem(
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.price,
            )
        )

    order = Order(total=total, items=order_items)
    db.add(order)
    await db.commit()
    await db.refresh(order, attribute_names=["items"])

    await messaging.publish(
        routing_key="order.created",
        body={"event": "order.created", "order_id": str(order.id)},
    )

    return order


@router.get("", response_model=list[OrderResponse])
async def list_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).order_by(Order.created_at.desc()))
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    await db.refresh(order, attribute_names=["items"])
    return order
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/orders-api && pytest tests/test_orders.py -v`
Expected: 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/orders-api/app/routers/orders.py apps/orders-api/tests/test_orders.py
git commit -m "feat(api): add orders endpoints with stock decrement and tests"
```

---

### Task 11: Health Router

**Files:**
- Modify: `apps/orders-api/app/routers/health.py`
- Create: `apps/orders-api/tests/test_health.py`

- [ ] **Step 1: Write tests**

```python
# apps/orders-api/tests/test_health.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/orders-api && pytest tests/test_health.py -v`
Expected: FAIL (health router is a stub)

- [ ] **Step 3: Implement health router**

```python
# apps/orders-api/app/routers/health.py
import json

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import messaging
from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    db_status = "up"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"

    rabbitmq_status = "up" if await messaging.is_healthy() else "down"

    is_healthy = db_status == "up" and rabbitmq_status == "up"
    return JSONResponse(
        status_code=200 if is_healthy else 503,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "database": db_status,
            "rabbitmq": rabbitmq_status,
        },
    )


@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})


@router.get("/metrics")
async def metrics():
    return PlainTextResponse("# placeholder — implemented in Phase 2\n")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/orders-api && pytest tests/test_health.py -v`
Expected: 4 tests PASS

- [ ] **Step 5: Run all API tests**

Run: `cd apps/orders-api && pytest tests/ -v`
Expected: All tests PASS (products + orders + health)

- [ ] **Step 6: Commit**

```bash
git add apps/orders-api/app/routers/health.py apps/orders-api/tests/test_health.py
git commit -m "feat(api): add health, ready, metrics endpoints with tests"
```

---

## Chunk 3: Seed + Worker + Docker

### Task 12: Seed Script

**Files:**
- Create: `apps/orders-api/seed.py`

- [ ] **Step 1: Create idempotent seed script**

```python
# apps/orders-api/seed.py
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
```

- [ ] **Step 2: Commit**

```bash
git add apps/orders-api/seed.py
git commit -m "feat(api): add idempotent product seed script"
```

---

### Task 13: Celery Worker

**Files:**
- Modify: `apps/worker/worker/celery_app.py`
- Modify: `apps/worker/worker/tasks.py`
- Create: `apps/worker/tests/conftest.py`
- Create: `apps/worker/tests/test_tasks.py`

- [ ] **Step 1: Write tests for process_order task**

```python
# apps/worker/tests/conftest.py
import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from worker.models import Order


@pytest.fixture
def mock_db():
    session = MagicMock()
    order = Order(
        id=uuid.uuid4(),
        status="pending",
        total=Decimal("29.99"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    session.get.return_value = order
    return session, order


@pytest.fixture
def mock_get_db(mock_db):
    session, order = mock_db
    with patch("worker.tasks.get_db") as mock:
        mock.return_value = iter([session])
        yield session, order
```

```python
# apps/worker/tests/test_tasks.py
import uuid
from unittest.mock import MagicMock, patch

import pytest


def test_process_order_success(mock_get_db):
    session, order = mock_get_db
    order_id = str(order.id)

    with patch("worker.tasks.publish_event") as mock_pub:
        from worker.tasks import process_order

        process_order(order_id)

    assert order.status == "completed"
    session.commit.assert_called()
    mock_pub.assert_called_once_with(
        "order.completed", {"event": "order.completed", "order_id": order_id}
    )


def test_process_order_not_found(mock_get_db):
    session, _ = mock_get_db
    session.get.return_value = None

    from worker.tasks import process_order

    with pytest.raises(ValueError, match="not found"):
        process_order(str(uuid.uuid4()))


def test_process_order_sets_processing_status(mock_get_db):
    session, order = mock_get_db
    statuses = []

    original_commit = session.commit
    def track_commit():
        statuses.append(order.status)
        original_commit()

    session.commit = MagicMock(side_effect=track_commit)

    with patch("worker.tasks.publish_event"):
        with patch("worker.tasks.time.sleep"):
            from worker.tasks import process_order
            process_order(str(order.id))

    assert "processing" in statuses
    assert order.status == "completed"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/worker && pip install -e ".[dev]" 2>/dev/null; pip install -e . 2>/dev/null; pytest tests/test_tasks.py -v`
Expected: FAIL (celery_app.py and tasks.py are empty/missing)

- [ ] **Step 3: Implement Celery app**

```python
# apps/worker/worker/celery_app.py
from celery import Celery
from kombu import Exchange, Queue

from worker.config import settings

app = Celery("worker")

app.conf.update(
    broker_url=settings.broker_url,
    result_backend=settings.result_backend,
    task_queues=[
        Queue(
            "order.created",
            Exchange("orders", type="direct"),
            routing_key="order.created",
        ),
    ],
    task_routes={
        "worker.tasks.process_order": {"queue": "order.created"},
    },
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
```

- [ ] **Step 4: Implement process_order task**

```python
# apps/worker/worker/tasks.py
import json
import logging
import time
from random import uniform

import pika

from worker.celery_app import app
from worker.config import settings
from worker.database import get_db
from worker.models import Order

logger = logging.getLogger(__name__)


def publish_event(routing_key: str, body: dict) -> None:
    connection = pika.BlockingConnection(
        pika.URLParameters(settings.broker_url)
    )
    channel = connection.channel()
    channel.basic_publish(
        exchange="orders",
        routing_key=routing_key,
        body=json.dumps(body),
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type="application/json",
        ),
    )
    connection.close()


@app.task(
    bind=True,
    name="worker.tasks.process_order",
    max_retries=3,
    autoretry_for=(ConnectionError, OSError),
    retry_backoff=10,
    retry_backoff_max=60,
)
def process_order(self, order_id: str) -> dict:
    logger.info("Processing order %s (attempt %d/%d)", order_id, self.request.retries + 1, self.max_retries + 1)

    import uuid as uuid_mod

    db = next(get_db())
    try:
        order = db.get(Order, uuid_mod.UUID(order_id))
        if order is None:
            raise ValueError(f"Order {order_id} not found")

        order.status = "processing"
        db.commit()
        logger.info("Order %s status: processing", order_id)

        time.sleep(uniform(2, 5))

        order.status = "completed"
        db.commit()
        logger.info("Order %s status: completed", order_id)

        publish_event(
            "order.completed",
            {"event": "order.completed", "order_id": order_id},
        )

        return {"order_id": order_id, "status": "completed"}
    except ValueError:
        # Permanent failure — don't retry
        logger.error("Order %s not found, marking as failed", order_id)
        raise
    except Exception:
        db.rollback()
        is_final_attempt = self.request.retries >= self.max_retries
        if is_final_attempt:
            order = db.get(Order, uuid_mod.UUID(order_id))
            if order and order.status != "completed":
                order.status = "failed"
                db.commit()
                logger.error("Order %s failed after all retries", order_id)
        raise
    finally:
        db.close()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd apps/worker && pytest tests/test_tasks.py -v`
Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add apps/worker/worker/celery_app.py apps/worker/worker/tasks.py apps/worker/tests/
git commit -m "feat(worker): add Celery app and process_order task with tests"
```

---

### Task 14: Dockerfiles

**Files:**
- Create: `apps/orders-api/Dockerfile`
- Create: `apps/orders-api/.dockerignore`
- Create: `apps/orders-api/entrypoint.sh`
- Create: `apps/worker/Dockerfile`
- Create: `apps/worker/.dockerignore`

- [ ] **Step 1: Create .dockerignore files for both apps**

```
# apps/orders-api/.dockerignore AND apps/worker/.dockerignore (same content)
__pycache__
*.pyc
.pytest_cache
tests/
.git
.gitignore
*.md
```

- [ ] **Step 2: Create API Dockerfile**

```dockerfile
# apps/orders-api/Dockerfile
FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
```

- [ ] **Step 3: Create API entrypoint**

```bash
#!/bin/sh
# apps/orders-api/entrypoint.sh
set -e

echo "Running migrations..."
alembic upgrade head

echo "Seeding products..."
python seed.py

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 4: Create Worker Dockerfile**

```dockerfile
# apps/worker/Dockerfile
FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

CMD ["celery", "-A", "worker.celery_app", "worker", "--loglevel=info"]
```

- [ ] **Step 5: Commit**

```bash
git add apps/orders-api/Dockerfile apps/orders-api/.dockerignore apps/orders-api/entrypoint.sh apps/worker/Dockerfile apps/worker/.dockerignore
git commit -m "feat: add Dockerfiles for api and worker"
```

---

### Task 15: Docker Compose

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Create docker-compose.yml**

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: orders
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  rabbitmq:
    image: rabbitmq:3.13-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
    ports:
      - "5672:5672"
      - "15672:15672"
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
      interval: 10s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  orders-api:
    build: ./apps/orders-api
    ports:
      - "8000:8000"
    environment:
      ORDERS_DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/orders
      ORDERS_RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672//
    depends_on:
      postgres:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  worker:
    build: ./apps/worker
    environment:
      WORKER_DATABASE_URL: postgresql+psycopg2://postgres:postgres@postgres:5432/orders
      WORKER_BROKER_URL: amqp://guest:guest@rabbitmq:5672//
      WORKER_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  postgres_data:
```

- [ ] **Step 2: Verify Docker Compose config is valid**

Run: `docker compose config --quiet`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add Docker Compose with all services"
```

---

### Task 16: Smoke Test — Full Stack

- [ ] **Step 1: Start all services**

Run: `docker compose up --build -d`
Expected: All 5 services start. Check with `docker compose ps`.

- [ ] **Step 2: Wait for healthy services**

Run: `docker compose ps` — verify all services are `Up (healthy)` or `Up`

- [ ] **Step 3: Test API endpoints**

```bash
# List products (should have 5 seeded)
curl -s http://localhost:8000/products | python -m json.tool

# Create an order
curl -s -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": "<id-from-products>", "quantity": 2}]}' | python -m json.tool

# Check order status (should be pending, then eventually completed)
curl -s http://localhost:8000/orders | python -m json.tool

# Health check
curl -s http://localhost:8000/health | python -m json.tool

# Readiness
curl -s http://localhost:8000/ready | python -m json.tool

# Metrics placeholder
curl -s http://localhost:8000/metrics
```

- [ ] **Step 4: Verify worker processed the order**

Wait ~5 seconds, then:
```bash
curl -s http://localhost:8000/orders | python -m json.tool
```
Expected: Order status should be `completed`.

- [ ] **Step 5: Check RabbitMQ management UI**

Open: http://localhost:15672 (guest/guest)
Verify: `order.created` and `order.completed` queues exist.

- [ ] **Step 6: Tear down**

Run: `docker compose down -v`

---

## Chunk 4: Integration Tests

### Task 17: Integration Tests with TestContainers

**Files:**
- Modify: `apps/orders-api/tests/test_integration.py`

- [ ] **Step 1: Write integration tests**

```python
# apps/orders-api/tests/test_integration.py
import asyncio
import time

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer
from testcontainers.rabbitmq import RabbitMqContainer

from app.database import get_db
from app.models import Base


@pytest.fixture(scope="module")
def postgres_container():
    with PostgresContainer("postgres:16-alpine", dbname="orders") as pg:
        yield pg


@pytest.fixture(scope="module")
def rabbitmq_container():
    with RabbitMqContainer("rabbitmq:3.13-management-alpine") as rmq:
        yield rmq


@pytest.fixture(scope="module")
def async_db_url(postgres_container):
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)
    user = postgres_container.username
    password = postgres_container.password
    dbname = postgres_container.dbname
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"


@pytest.fixture
async def integration_engine(async_db_url):
    engine = create_async_engine(async_db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def integration_session(integration_engine):
    session_factory = async_sessionmaker(
        integration_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def integration_client(integration_session, rabbitmq_container):
    from unittest.mock import AsyncMock, patch

    from app.main import app

    async def override_get_db():
        yield integration_session

    app.dependency_overrides[get_db] = override_get_db

    rmq_host = rabbitmq_container.get_container_host_ip()
    rmq_port = rabbitmq_container.get_exposed_port(5672)
    rmq_url = f"amqp://guest:guest@{rmq_host}:{rmq_port}//"

    with patch("app.config.settings") as mock_settings:
        mock_settings.rabbitmq_url = rmq_url
        mock_settings.database_url = "unused"
        mock_settings.app_name = "orders-api"

        with patch("app.messaging.connect", new_callable=AsyncMock):
            with patch("app.messaging.disconnect", new_callable=AsyncMock):
                with patch("app.messaging.is_healthy", new_callable=AsyncMock, return_value=True):
                    with patch("app.messaging.publish", new_callable=AsyncMock):
                        transport = ASGITransport(app=app)
                        async with AsyncClient(
                            transport=transport, base_url="http://test"
                        ) as ac:
                            yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_integration_health(integration_client):
    response = await integration_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_integration_ready(integration_client):
    response = await integration_client.get("/ready")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_integration_products_empty(integration_client):
    response = await integration_client.get("/products")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_integration_seed_and_order_flow(integration_client, integration_session):
    from decimal import Decimal
    from app.models import Product

    product = Product(
        name="Integration Widget",
        price=Decimal("15.00"),
        stock=50,
        description="Test product",
    )
    integration_session.add(product)
    await integration_session.commit()
    await integration_session.refresh(product)

    # List products
    response = await integration_client.get("/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 1

    # Create order
    response = await integration_client.post(
        "/orders",
        json={"items": [{"product_id": str(product.id), "quantity": 3}]},
    )
    assert response.status_code == 201
    order = response.json()
    assert order["status"] == "pending"
    assert order["total"] == "45.00"

    # Get order
    response = await integration_client.get(f"/orders/{order['id']}")
    assert response.status_code == 200
    assert response.json()["items"][0]["quantity"] == 3

    # Verify stock decremented
    response = await integration_client.get(f"/products/{product.id}")
    assert response.json()["stock"] == 47
```

- [ ] **Step 2: Run integration tests**

Run: `cd apps/orders-api && pytest tests/test_integration.py -v --timeout=60`
Expected: All integration tests PASS (requires Docker running)

- [ ] **Step 3: Run full test suite**

Run: `cd apps/orders-api && pytest tests/ -v`
Expected: All unit + integration tests PASS

- [ ] **Step 4: Commit**

```bash
git add apps/orders-api/tests/test_integration.py
git commit -m "test(api): add integration tests with TestContainers"
```

---

## Verification Checklist

After all tasks are complete, verify:

- [ ] `docker compose up --build -d` starts all services successfully
- [ ] `curl localhost:8000/products` returns 5 seeded products
- [ ] `POST /orders` creates an order and returns 201
- [ ] Order status transitions: pending → processing → completed (within ~5s)
- [ ] `GET /health` returns healthy when all services are up
- [ ] `GET /ready` returns ready
- [ ] `GET /metrics` returns placeholder text
- [ ] Stock is decremented after order creation
- [ ] Invalid orders (bad product, insufficient stock) return proper errors
- [ ] Unit tests pass: `cd apps/orders-api && pytest tests/ -v --ignore=tests/test_integration.py`
- [ ] Integration tests pass: `cd apps/orders-api && pytest tests/test_integration.py -v`
- [ ] Worker tests pass: `cd apps/worker && pytest tests/ -v`
