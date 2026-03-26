import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.metrics import REQUEST_COUNT, REQUEST_DURATION, REQUESTS_IN_PROGRESS


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        # Normalize path: replace UUIDs with {id}
        path = request.url.path
        parts = path.strip("/").split("/")
        normalized = []
        for part in parts:
            if len(part) == 36 and part.count("-") == 4:
                normalized.append("{id}")
            else:
                normalized.append(part)
        endpoint = "/" + "/".join(normalized) if normalized else "/"

        REQUESTS_IN_PROGRESS.labels(method=method).inc()
        start = time.perf_counter()

        try:
            response = await call_next(request)
            status = str(response.status_code)
        except Exception:
            status = "500"
            raise
        finally:
            duration = time.perf_counter() - start
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
            REQUEST_DURATION.labels(method=method, endpoint=endpoint, status=status).observe(duration)
            REQUESTS_IN_PROGRESS.labels(method=method).dec()

        return response
