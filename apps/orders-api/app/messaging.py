from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

import aio_pika

from app.config import settings

logger = logging.getLogger(__name__)

_connection: Optional[aio_pika.abc.AbstractRobustConnection] = None
_channel: Optional[aio_pika.abc.AbstractChannel] = None
_orders_exchange: Optional[aio_pika.abc.AbstractExchange] = None


async def connect() -> None:
    global _connection, _channel, _orders_exchange
    _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    _channel = await _connection.channel()

    orders_exchange = await _channel.declare_exchange(
        "orders", aio_pika.ExchangeType.DIRECT, durable=True
    )
    dlx_exchange = await _channel.declare_exchange(
        "orders.dlx", aio_pika.ExchangeType.DIRECT, durable=True
    )

    dlq = await _channel.declare_queue("order.created.dlq", durable=True)
    await dlq.bind(dlx_exchange, routing_key="order.created")

    queue = await _channel.declare_queue(
        "order.created",
        durable=True,
        arguments={
            "x-dead-letter-exchange": "orders.dlx",
            "x-dead-letter-routing-key": "order.created",
        },
    )
    await queue.bind(orders_exchange, routing_key="order.created")

    completed_queue = await _channel.declare_queue(
        "order.completed",
        durable=True,
        arguments={"x-message-ttl": 86400000},
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


async def publish_task(task_name: str, args: list, routing_key: str) -> None:
    """Publish a message in Celery v2 protocol format."""
    if _orders_exchange is None:
        raise RuntimeError("RabbitMQ not connected")

    task_id = str(uuid.uuid4())
    # Celery v2 protocol: body is [args, kwargs, embed]
    celery_body = [args, {}, {"callbacks": None, "errbacks": None, "chain": None}]

    message = aio_pika.Message(
        body=json.dumps(celery_body).encode(),
        content_type="application/json",
        content_encoding="utf-8",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        headers={
            "lang": "py",
            "task": task_name,
            "id": task_id,
            "root_id": task_id,
            "parent_id": None,
            "group": None,
        },
    )
    await _orders_exchange.publish(message, routing_key=routing_key)
    logger.info("Published task %s [%s]: %s", task_name, task_id, args)


async def is_healthy() -> bool:
    return _connection is not None and not _connection.is_closed
