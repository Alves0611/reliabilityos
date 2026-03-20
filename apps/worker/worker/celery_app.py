from celery import Celery
from celery.signals import setup_logging as celery_setup_logging
from kombu import Exchange, Queue

from worker.config import settings
from worker.telemetry import setup_telemetry

setup_telemetry()


@celery_setup_logging.connect
def on_setup_logging(**kwargs):
    """Override Celery's logging to use our JSON formatter."""
    from worker.logging_config import setup_logging
    setup_logging()


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
