import asyncio
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.metrics import REQUEST_COUNT, REQUEST_DURATION, REQUESTS_IN_PROGRESS


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
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
            from app.routers.chaos import get_latency_seconds, should_fail

            latency = get_latency_seconds()
            if latency > 0 and not path.startswith("/chaos"):
                await asyncio.sleep(latency)

            if should_fail() and not path.startswith(("/chaos", "/health", "/ready", "/metrics")):
                response = JSONResponse(status_code=500, content={"detail": "Injected chaos error"})
                status = "500"
            else:
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
