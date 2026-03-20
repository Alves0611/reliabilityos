from prometheus_client import Counter, Histogram

ORDERS_PROCESSED = Counter(
    "orders_processed_total",
    "Total orders processed by worker",
    ["status"],
)

ORDER_PROCESSING_DURATION = Histogram(
    "order_processing_duration_seconds",
    "Time to process an order end-to-end",
    buckets=[1.0, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0, 15.0, 30.0],
)
