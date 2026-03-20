# Phase 1 — Application Core Design

## Overview

Phase 1 delivers the base application for ReliabilityOS: a FastAPI orders API + Celery worker processing orders asynchronously via RabbitMQ, backed by PostgreSQL. All services run locally via Docker Compose.

The app is intentionally simple — it exists as a target for the SRE infrastructure built in later phases. Business logic is minimal: products are seeded, orders go through a status machine (pending → processing → completed/failed).

## Architecture

```
Client → FastAPI (orders-api:8000)
              │
              ├── GET /products         → list seeded products
              ├── GET /products/{id}    → product detail
              ├── POST /orders          → create order + publish to RabbitMQ
              ├── GET /orders           → list orders
              ├── GET /orders/{id}      → order detail with status
              ├── GET /health           → liveness (DB + RabbitMQ reachable)
              ├── GET /ready            → readiness (DB connected)
              └── GET /metrics          → placeholder (stub for Phase 2)

RabbitMQ ← message "order.created" { order_id }
    │
    ▼
Celery Worker
    ├── Consume "order.created"
    ├── Update status: pending → processing
    ├── Simulate processing (sleep 2-5s)
    ├── Update status: processing → completed
    └── Publish event "order.completed" to RabbitMQ
```

## Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| API Framework | FastAPI + Uvicorn | Async, modern, OpenAPI docs built-in |
| ORM (API) | SQLAlchemy 2.0 async + asyncpg | Industry standard, mature ecosystem |
| ORM (Worker) | SQLAlchemy 2.0 sync + psycopg2 | Celery is sync — async adds complexity without benefit |
| Migrations | Alembic | Standard for SQLAlchemy, reliable |
| Task Queue | Celery 5.x | Battle-tested, native RabbitMQ support |
| Message Broker | RabbitMQ 3.13 | Required by roadmap, robust AMQP broker |
| Result Backend | Redis 7 | Fast, simple, Celery-native |
| Database | PostgreSQL 16 | Required by roadmap |
| MQ Publishing | aio-pika | Async AMQP publishing from API, non-blocking, decoupled from Celery |
| Validation | Pydantic v2 | FastAPI-native, fast serialization |
| Config | pydantic-settings | Env-based config with validation |
| Testing | pytest + TestContainers | Real containers for integration tests |
| Containerization | Docker + Docker Compose | Local dev infra |

## Data Model

### Product
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK, server-generated |
| name | VARCHAR(255) | NOT NULL |
| description | TEXT | nullable |
| price | DECIMAL(10,2) | NOT NULL, > 0 |
| stock | INTEGER | NOT NULL, >= 0 |
| created_at | TIMESTAMP | server default |

### Order
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK, server-generated |
| status | VARCHAR(20) | pending / processing / completed / failed |
| total | DECIMAL(10,2) | calculated from items |
| created_at | TIMESTAMP | server default |
| updated_at | TIMESTAMP | on update |

### OrderItem
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| order_id | UUID | FK → Order |
| product_id | UUID | FK → Product |
| quantity | INTEGER | > 0 |
| unit_price | DECIMAL(10,2) | snapshot from product at order time |

## API Contracts

### POST /orders
```json
// Request
{
  "items": [
    {"product_id": "uuid", "quantity": 2},
    {"product_id": "uuid", "quantity": 1}
  ]
}

// Response 201
{
  "id": "uuid",
  "status": "pending",
  "total": 59.97,
  "items": [...],
  "created_at": "2026-03-19T..."
}

// Error 422 — validation failure
// Error 400 — product not found or insufficient stock
```

Stock is decremented at order creation time (inside the same DB transaction that creates the order). This is an optimistic approach — if the worker later fails after all retries, stock is NOT restored (failed orders require manual review). This keeps the implementation simple and avoids race conditions where two orders could claim the same stock.

### GET /products
```json
// Response 200
[
  {
    "id": "uuid",
    "name": "Widget Pro",
    "price": 29.99,
    "stock": 100,
    "description": "A reliable widget"
  }
]
```

### GET /orders
```json
// Response 200
[
  {
    "id": "uuid",
    "status": "completed",
    "total": 59.97,
    "created_at": "2026-03-19T...",
    "updated_at": "2026-03-19T..."
  }
]
```

No pagination in Phase 1 — simple list ordered by `created_at DESC`.

### GET /orders/{id}
```json
// Response 200
{
  "id": "uuid",
  "status": "completed",
  "total": 59.97,
  "items": [
    {
      "id": "uuid",
      "product_id": "uuid",
      "quantity": 2,
      "unit_price": 29.99
    }
  ],
  "created_at": "2026-03-19T...",
  "updated_at": "2026-03-19T..."
}

// Error 404 — order not found
```

### GET /health
```json
// Response 200
{"status": "healthy", "database": "up", "rabbitmq": "up"}

// Response 503
{"status": "unhealthy", "database": "up", "rabbitmq": "down"}
```

### GET /ready
```json
{"status": "ready"}  // 200
{"status": "not_ready"}  // 503
```

### GET /metrics
```text
# placeholder — implemented in Phase 2
```

## RabbitMQ Topology

| Resource | Name | Config |
|---|---|---|
| Exchange | `orders` | type: `direct`, durable: true |
| Queue | `order.created` | durable: true, bound to `orders` exchange with routing key `order.created` |
| Queue | `order.completed` | durable: true, bound to `orders` exchange with routing key `order.completed` |
| Dead Letter Exchange | `orders.dlx` | type: `direct`, durable: true |
| Dead Letter Queue | `order.created.dlq` | durable: true, bound to `orders.dlx` with routing key `order.created` |

The `order.created` queue is configured with `x-dead-letter-exchange: orders.dlx` and `x-dead-letter-routing-key: order.created`. Messages that exhaust all Celery retries are routed to the DLQ for inspection.

The `order.completed` queue has no consumer in Phase 1 — it exists as a stub for future phases (e.g., notifications, analytics). Messages accumulate but the queue has a TTL of 24h to prevent unbounded growth.

## Celery Configuration

```python
# Celery connects to RabbitMQ as its broker
broker_url = "amqp://guest:guest@rabbitmq:5672//"
result_backend = "redis://redis:6379/0"

# Task routing: bind process_order task to the order.created AMQP queue
task_queues = [
    Queue("order.created", Exchange("orders", type="direct"), routing_key="order.created"),
]
task_routes = {
    "worker.tasks.process_order": {"queue": "order.created"},
}

# Retry config
task_acks_late = True
task_reject_on_worker_lost = True
worker_prefetch_multiplier = 1
```

The worker consumes directly from the `order.created` AMQP queue. `task_acks_late = True` ensures messages are only acknowledged after successful processing, preventing message loss on worker crash.

## Message Flow

1. `POST /orders` → API validates items, checks products exist, decrements stock, calculates total
2. API saves Order (status=pending) + OrderItems to PostgreSQL in a transaction
3. API publishes `{"event": "order.created", "order_id": "uuid"}` to RabbitMQ exchange `orders` with routing key `order.created`
4. API returns 201 with order data immediately (async processing)
5. Celery worker consumes from `order.created` queue
6. Worker updates order status to `processing`
7. Worker simulates processing (random sleep 2-5s)
8. Worker updates order status to `completed`
9. Worker publishes `{"event": "order.completed", "order_id": "uuid"}` to RabbitMQ (no consumer in Phase 1)

**Failure handling:** If worker fails during processing, Celery retries with exponential backoff (max 3 retries, delays: 10s, 30s, 60s). After all retries are exhausted, the order status is set to `failed` and the message is routed to the dead-letter queue.

## File Structure

```
apps/
├── orders-api/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, lifespan, router includes
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # async engine, session factory
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── messaging.py         # RabbitMQ publisher (aio-pika, async)
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── products.py      # GET /products, GET /products/{id}
│   │       ├── orders.py        # POST /orders, GET /orders, GET /orders/{id}
│   │       └── health.py        # GET /health, GET /ready, GET /metrics
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── conftest.py          # fixtures, test client
│   │   ├── test_products.py     # unit tests
│   │   ├── test_orders.py       # unit tests
│   │   └── test_integration.py  # TestContainers (PG + RabbitMQ + Redis)
│   ├── seed.py                  # Seed products into DB
│   ├── Dockerfile
│   └── pyproject.toml
├── worker/
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── celery_app.py        # Celery app config
│   │   ├── config.py            # Settings
│   │   ├── tasks.py             # process_order task
│   │   └── database.py          # sync SQLAlchemy engine + session
│   ├── tests/
│   │   ├── conftest.py
│   │   └── test_tasks.py
│   ├── Dockerfile
│   └── pyproject.toml
docker-compose.yml
```

## Docker Compose Services

| Service | Image | Ports | Depends On |
|---|---|---|---|
| postgres | postgres:16-alpine | 5432 | — |
| rabbitmq | rabbitmq:3.13-management-alpine | 5672, 15672 | — |
| redis | redis:7-alpine | 6379 | — |
| orders-api | build ./apps/orders-api | 8000 | postgres, rabbitmq |
| worker | build ./apps/worker | — | postgres, rabbitmq, redis |

Note: `orders-api` does NOT depend on Redis — Redis is only used as Celery's result backend. The API publishes to RabbitMQ directly via pika.

## Startup Sequence

1. Docker Compose starts `postgres`, `rabbitmq`, `redis` first
2. `orders-api` entrypoint runs: `alembic upgrade head && python seed.py && uvicorn app.main:app`
   - Alembic applies all pending migrations
   - `seed.py` is idempotent (uses `INSERT ... ON CONFLICT DO NOTHING` on product name)
   - Then starts Uvicorn
3. `worker` entrypoint runs: `celery -A worker.celery_app worker --loglevel=info`
   - Worker shares the same DB models as the API but uses sync SQLAlchemy
   - Worker declares its queues on startup via Celery's `task_queues` config

## Seed Data

5 products seeded via `seed.py`:

1. Widget Pro — $29.99 (stock: 100)
2. Gadget Ultra — $49.99 (stock: 50)
3. Connector Basic — $9.99 (stock: 200)
4. Sensor Max — $79.99 (stock: 30)
5. Module Core — $19.99 (stock: 150)

## Testing Strategy

### Unit Tests (pytest)
- Mock database and RabbitMQ
- Test API endpoint logic, validation, error cases
- Test Celery task logic with mocked DB

### Integration Tests (TestContainers)
- Real PostgreSQL, RabbitMQ, Redis containers
- Test full flow: create order → worker processes → status updated
- Test health/ready endpoints against real services
- Test seed script populates products

## Design Decisions

1. **aio-pika for RabbitMQ publishing (not Celery send_task):** Separates the API's publishing concern from Celery's consumption. The API publishes AMQP messages directly using `aio-pika` (async wrapper around pika) to avoid blocking FastAPI's event loop. Celery consumes them as a worker. This allows future flexibility (other consumers, different message formats).

2. **Sync SQLAlchemy in Worker:** Celery workers are fundamentally synchronous. Using async SQLAlchemy inside Celery requires running an event loop per task, adding complexity with no performance benefit since Celery already handles concurrency via prefork/threads.

3. **UUID primary keys:** Prevents enumeration attacks, works well in distributed systems (future multi-cluster in Phase 14).

4. **Price snapshot in OrderItem:** `unit_price` captures the price at order time, not a live reference. Products can change price without affecting historical orders.

5. **Separate pyproject.toml per app:** Each app has its own dependencies, allowing independent Docker builds and avoiding dependency conflicts.
