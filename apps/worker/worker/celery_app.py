from celery import Celery
from kombu import Exchange, Queue

from worker.config import settings

app = Celery("worker")

app.conf.update(
    imports=["worker.tasks"],
    broker_url=settings.broker_url,
    result_backend=settings.result_backend,
    task_queues=[
        Queue(
            "order.created",
            Exchange("orders", type="direct"),
            routing_key="order.created",
            queue_arguments={
                "x-dead-letter-exchange": "orders.dlx",
                "x-dead-letter-routing-key": "order.created",
            },
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
