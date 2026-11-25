import time
import threading
from collections import defaultdict, deque
from typing import Deque, Dict
from fastapi import Request

from app.config import settings
from app.errors import BusinessException


class SlidingWindowRateLimiter:
    """
    In-memory thread-safe sliding window rate limiter (F21, NFR-16).
    Tracks timestamps per key within a 60-second window.
    """

    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: int = 60) -> None:
        if not settings.RATE_LIMIT_ENABLED or limit <= 0:
            return

        now = time.monotonic()
        cutoff = now - window_seconds

        with self._lock:
            q = self._hits[key]
            while q and q[0] <= cutoff:
                q.popleft()

            if len(q) >= limit:
                raise BusinessException(
                    code="RATE_LIMITED",
                    detail=f"Quá nhiều yêu cầu ({limit} lần/{window_seconds}s). Vui lòng thử lại sau."
                )

            q.append(now)


rate_limiter = SlidingWindowRateLimiter()


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_login(request: Request) -> None:
    ip = get_client_ip(request)
    rate_limiter.check(f"login:{ip}", limit=settings.RATE_LIMIT_LOGIN_PER_MIN, window_seconds=60)


def rate_limit_api(request: Request) -> None:
    api_key = request.headers.get("X-API-Key")
    if api_key:
        rate_limiter.check(f"apikey:{api_key}", limit=settings.RATE_LIMIT_API_PER_MIN, window_seconds=60)
    else:
        ip = get_client_ip(request)
        rate_limiter.check(f"ip:{ip}", limit=settings.RATE_LIMIT_API_PER_MIN, window_seconds=60)
