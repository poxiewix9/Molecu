"""Rate limiting middleware using a token-bucket algorithm.

Limits concurrent and per-interval requests to the SSE evaluation endpoint,
preventing unbounded resource consumption under concurrent load.
"""

import time
import asyncio
import logging
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

log = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limiter keyed by client IP.

    Configurable via constructor for easy tuning in staging vs production.
    Default: 5 requests per 60-second window per IP for the evaluate endpoint,
    20 requests per 60-second window for all other API endpoints.
    """

    def __init__(
        self,
        app,
        evaluate_limit: int = 5,
        general_limit: int = 20,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        self.evaluate_limit = evaluate_limit
        self.general_limit = general_limit
        self.window = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if not path.startswith("/api/"):
            return await call_next(request)

        ip = self._client_ip(request)
        is_evaluate = path.startswith("/api/evaluate/")
        limit = self.evaluate_limit if is_evaluate else self.general_limit
        bucket_key = f"{ip}:{'evaluate' if is_evaluate else 'general'}"

        async with self._lock:
            now = time.monotonic()
            window_start = now - self.window
            self._buckets[bucket_key] = [
                t for t in self._buckets[bucket_key] if t > window_start
            ]

            if len(self._buckets[bucket_key]) >= limit:
                retry_after = int(self.window - (now - self._buckets[bucket_key][0])) + 1
                log.warning(
                    "Rate limit exceeded for %s on %s (%d/%d in %ds window)",
                    ip, path, len(self._buckets[bucket_key]), limit, self.window,
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded. Please wait before making another request.",
                        "retry_after_seconds": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

            self._buckets[bucket_key].append(now)

        return await call_next(request)
