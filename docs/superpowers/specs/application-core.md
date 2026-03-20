# ReliabilityOS — Application Design

## Overview

ReliabilityOS is a portfolio SRE project: a FastAPI orders API + Celery worker processing orders asynchronously via RabbitMQ, backed by PostgreSQL. All services run locally via Docker Compose.

The app is intentionally simple — it exists as a target for the SRE infrastructure built in later phases. Business logic is minimal: products are seeded, orders go through a status machine (pending → processing → completed/failed).

Includes a single-page dashboard frontend, Prometheus metrics, structured JSON logs, and OpenTelemetry traces.

## Architecture

```
Browser (static/index.html)
    │
    ▼
FastAPI (orders-api:8000)
    │
    ├── GET /products         → list seeded products
    ├── GET /products/{id}    → product detail
    ├── POST /orders          → create order + publish to RabbitMQ
    ├── GET /orders           → list orders
    ├── GET /orders/{id}      → order detail with status
    ├── GET /health           → liveness (DB + RabbitMQ reachable)
    ├── GET /ready            → readiness (DB connected)
    ├── GET /metrics          → Prometheus exposition format
    └── GET /                 → Dashboard frontend

RabbitMQ ← Celery v2 protocol message [order_id]
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
| MQ Publishing | aio-pika | Async AMQP publishing from API, non-blocking, Celery v2 protocol format |
| Validation | Pydantic v2 | FastAPI-native, fast serialization |
| Config | pydantic-settings | Env-based config with validation |
| Metrics | prometheus-client | Prometheus exposition format |
| Traces | OpenTelemetry SDK | Auto + manual instrumentation, console exporter |
| Logs | python-json-logger | Structured JSON with trace correlation |
| Testing | pytest + TestContainers | Real containers for integration tests |
| Containerization | Docker + Docker Compose | Local dev infra |
| Frontend | Single HTML file | Vanilla JS, served by FastAPI StaticFiles |

## Data Model

### Product
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK, server-generated |
| name | VARCHAR(255) | NOT NULL, unique |
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
  "created_at": "2026-03-20T..."
}

// Error 422 — validation failure
// Error 400 — product not found or insufficient stock
```

Stock is decremented at order creation time (inside the same DB transaction that creates the order). This is an optimistic approach — if the worker later fails after all retries, stock is NOT restored (failed orders require manual review).

### GET /health
```json
{"status": "healthy", "database": "up", "rabbitmq": "up"}   // 200
{"status": "unhealthy", "database": "up", "rabbitmq": "down"} // 503
```

### GET /metrics
Prometheus exposition format with RED metrics and business metrics (see Instrumentation section).

## RabbitMQ Topology

| Resource | Name | Config |
|---|---|---|
| Exchange | `orders` | type: `direct`, durable: true |
| Queue | `order.created` | durable: true, DLX: `orders.dlx` |
| Queue | `order.completed` | durable: true, TTL: 24h |
| Dead Letter Exchange | `orders.dlx` | type: `direct`, durable: true |
| Dead Letter Queue | `order.created.dlq` | durable: true |

## Message Flow

1. `POST /orders` → API validates items, decrements stock, saves Order (status=pending)
2. API publishes Celery v2 protocol message via `publish_task()` (aio-pika) to `orders` exchange with routing key `order.created`
3. API returns 201 immediately
4. Celery worker consumes from `order.created` queue
5. Worker updates status to `processing`, sleeps 2-5s, updates to `completed`
6. Worker publishes raw `order.completed` event via pika

**Failure handling:** Celery retries with exponential backoff (max 3 retries, delays: 10s, 30s, 60s). After exhaustion, status = `failed`, message → DLQ.

## Frontend Dashboard

Single HTML file (`static/index.html`) served by FastAPI StaticFiles. Dark-mode SaaS layout with three columns:

- **Products** — card grid, click to add to cart
- **New Order** — cart with qty controls, place order button
- **Live Orders** — real-time status tracking via polling (2s interval), health indicators (5s interval)

Status transitions animate visually: pending (blue pulse) → processing (yellow pulse) → completed (green glow).

## Instrumentation

### Prometheus Metrics

**RED (HTTP middleware):**
- `http_requests_total` — Counter(method, endpoint, status)
- `http_request_duration_seconds` — Histogram(method, endpoint)
- `http_requests_in_progress` — Gauge(method)

**Business:**
- `orders_total` — Counter(status)
- `order_processing_duration_seconds` — Histogram (worker)
- `product_stock_units` — Gauge(product_name)

UUID paths normalized to `{id}` in labels.

### Structured Logs (JSON)

JSON on stdout via `python-json-logger`. Each line includes: timestamp, level, service, trace_id, span_id, plus contextual fields (order_id, duration_ms). Trace context extracted from OTel automatically.

### OpenTelemetry Traces

Auto-instrumentation: FastAPIInstrumentor, SQLAlchemyInstrumentor.
Manual spans: `create_order` (API), `process_order` (worker).
Exporter: ConsoleSpanExporter (stdout). Ready for Phase 3 to switch to OTLP → Collector → Tempo.

## Celery Configuration

```python
broker_url = "amqp://guest:guest@rabbitmq:5672//"
result_backend = "redis://redis:6379/0"
task_queues = [Queue("order.created", Exchange("orders", type="direct"), routing_key="order.created",
               queue_arguments={"x-dead-letter-exchange": "orders.dlx", "x-dead-letter-routing-key": "order.created"})]
task_acks_late = True
task_reject_on_worker_lost = True
worker_prefetch_multiplier = 1
```

Logging overridden via `setup_logging` Celery signal to use JSON formatter in worker processes.

## File Structure

```
apps/
├── orders-api/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, lifespan, instrumentation init
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # async engine, session factory
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── messaging.py         # RabbitMQ publisher (aio-pika, publish + publish_task)
│   │   ├── telemetry.py         # OTel tracer setup + auto-instrumentors
│   │   ├── metrics.py           # Prometheus metric definitions
│   │   ├── middleware.py        # Request metrics middleware
│   │   ├── logging_config.py    # JSON log formatter with trace context
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── products.py      # GET /products, GET /products/{id}
│   │       ├── orders.py        # POST /orders, GET /orders, GET /orders/{id}
│   │       └── health.py        # GET /health, GET /ready, GET /metrics
│   ├── static/
│   │   └── index.html           # Dashboard frontend (single file)
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_products.py
│   │   ├── test_orders.py
│   │   └── test_health.py
│   ├── seed.py                  # Idempotent product seeder
│   ├── entrypoint.sh            # alembic upgrade + seed + uvicorn
│   ├── Dockerfile
│   ├── .dockerignore
│   └── pyproject.toml
├── worker/
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── celery_app.py        # Celery app config + logging signal
│   │   ├── config.py            # Settings
│   │   ├── database.py          # sync SQLAlchemy engine + session
│   │   ├── models.py            # Same models (sync base)
│   │   ├── tasks.py             # process_order task
│   │   ├── telemetry.py         # OTel tracer setup
│   │   ├── metrics.py           # Worker metrics
│   │   └── logging_config.py    # JSON log formatter
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── test_tasks.py
│   ├── Dockerfile
│   ├── .dockerignore
│   └── pyproject.toml
docker-compose.yml
```

## Docker Compose Services

| Service | Image | Ports | Depends On |
|---|---|---|---|
| postgres | postgres:16-alpine | 5434:5432 | — |
| rabbitmq | rabbitmq:3.13-management-alpine | 5672, 15672 | — |
| redis | redis:7-alpine | 6380:6379 | — |
| orders-api | build ./apps/orders-api | 8000 | postgres, rabbitmq |
| worker | build ./apps/worker | — | postgres, rabbitmq, redis |

## Seed Data

8 products seeded via `seed.py` (idempotent, ON CONFLICT DO NOTHING):

1. Banana Orgânica — $2.49 (stock: 120)
2. Ovos Caipira — $5.99 (stock: 80)
3. Abacate Hass — $1.89 (stock: 200)
4. Pão de Fermentação Natural — $6.50 (stock: 40)
5. Iogurte Grego — $4.29 (stock: 150)
6. Salmão Atlântico — $12.99 (stock: 30)
7. Tomate Cereja — $3.49 (stock: 90)
8. Leite de Aveia — $3.99 (stock: 100)

## Design Decisions

1. **aio-pika with Celery v2 protocol format:** API publishes messages in Celery's wire protocol via `publish_task()`, allowing the worker to consume them as native Celery tasks. Decouples publishing from Celery's internals while maintaining compatibility.

2. **Sync SQLAlchemy in Worker:** Celery workers are fundamentally synchronous. Async adds complexity with no benefit.

3. **UUID primary keys:** Prevents enumeration attacks, works in distributed systems.

4. **Price snapshot in OrderItem:** `unit_price` captures price at order time.

5. **Separate pyproject.toml per app:** Independent dependencies and Docker builds.

6. **Single HTML frontend:** No build step, no JS framework. Vanilla JS with fetch + polling. Served as static file by FastAPI.

7. **Console span exporter:** Traces go to stdout in dev. Phase 3 switches to OTLP → Collector → Tempo without code changes.

8. **Celery logging signal:** Override Celery's logging via `setup_logging.connect` to ensure JSON formatter applies to forked worker processes.

## Out of Scope (Later Phases)

- Grafana dashboards + Tempo backend (Phase 3)
- Kubernetes manifests (Phase 4+)
- CI/CD pipeline (Phase 4)
