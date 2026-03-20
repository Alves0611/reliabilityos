from prometheus_client import Counter, Gauge, Histogram

# RED metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method"],
)

# Business metrics
ORDERS_TOTAL = Counter(
    "orders_total",
    "Total orders created",
    ["status"],
)

PRODUCT_STOCK = Gauge(
    "product_stock_units",
    "Current stock level per product",
    ["product_name"],
)
