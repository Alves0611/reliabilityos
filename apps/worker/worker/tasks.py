import json
import logging
import time
import uuid as uuid_mod
from random import uniform

import pika

from worker.celery_app import app
from worker.config import settings
from worker.database import get_db
from worker.models import Order

logger = logging.getLogger(__name__)


def publish_event(routing_key: str, body: dict) -> None:
    # Ensure URL ends with %2F for vhost '/' (pika URLParameters quirk)
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
    logger.info(
        "Processing order %s (attempt %d/%d)",
        order_id,
        self.request.retries + 1,
        self.max_retries + 1,
    )

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
        logger.error("Order %s not found, not retrying", order_id)
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
