import json
import logging
import time
import uuid as uuid_mod
from random import uniform

import pika

from worker.celery_app import app
from worker.config import settings
from worker.database import get_db
from worker.metrics import ORDER_PROCESSING_DURATION, ORDERS_PROCESSED
from worker.models import Order
from worker.telemetry import get_tracer

logger = logging.getLogger(__name__)
tracer = get_tracer()


def publish_event(routing_key: str, body: dict) -> None:
    broker_url = settings.broker_url
    if broker_url.endswith("//"):
        broker_url = broker_url[:-1] + "%2F"
    connection = pika.BlockingConnection(
        pika.URLParameters(broker_url)
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
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("celery.retry", self.request.retries)
        start_time = time.perf_counter()

        logger.info(
            "Processing order",
            extra={
                "order_id": order_id,
                "attempt": self.request.retries + 1,
                "max_attempts": self.max_retries + 1,
            },
        )

        db = next(get_db())
        try:
            order = db.get(Order, uuid_mod.UUID(order_id))
            if order is None:
                raise ValueError(f"Order {order_id} not found")

            order.status = "processing"
            db.commit()
            logger.info("Order status changed", extra={"order_id": order_id, "status": "processing"})

            processing_time = uniform(2, 5)
            span.set_attribute("order.processing_time_seconds", processing_time)
            time.sleep(processing_time)

            order.status = "completed"
            db.commit()

            duration = time.perf_counter() - start_time
            ORDER_PROCESSING_DURATION.labels(status="completed").observe(duration)
            ORDERS_PROCESSED.labels(status="completed").inc()

            logger.info(
                "Order completed",
                extra={"order_id": order_id, "status": "completed", "duration_ms": round(duration * 1000)},
            )

            publish_event(
                "order.completed",
                {"event": "order.completed", "order_id": order_id},
            )

            return {"order_id": order_id, "status": "completed"}
        except ValueError:
            ORDERS_PROCESSED.labels(status="failed").inc()
            span.set_attribute("error", True)
            logger.error("Order not found, not retrying", extra={"order_id": order_id})
            raise
        except Exception:
            db.rollback()
            span.set_attribute("error", True)
            is_final_attempt = self.request.retries >= self.max_retries
            if is_final_attempt:
                order = db.get(Order, uuid_mod.UUID(order_id))
                if order and order.status != "completed":
                    order.status = "failed"
                    db.commit()
                    ORDERS_PROCESSED.labels(status="failed").inc()
                    logger.error("Order failed after all retries", extra={"order_id": order_id})
            raise
        finally:
            db.close()
