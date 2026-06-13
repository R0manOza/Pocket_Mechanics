"""
In-process rate limiter (fixed window) for the chat endpoints.

No external dependency: a fixed-window counter per client IP. When the limit is
exceeded it raises a structured HTTP 429 with a `retry_after_seconds` field in
the body and a matching `Retry-After` header.

Configure via env:
  RATE_LIMIT_REQUESTS        (default 30)
  RATE_LIMIT_WINDOW_SECONDS  (default 60)

Disabled automatically under pytest (POCKET_MECHANICS_UNDER_TEST) so the test
suite and CI aren't throttled.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict

from fastapi import HTTPException, Request

_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", "30"))
_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))

# client_key -> [window_start_epoch, count]
_buckets: dict[str, list] = defaultdict(lambda: [0.0, 0])


def _client_key(request: Request) -> str:
    # Behind Render/Vercel the real client IP is in X-Forwarded-For.
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(request: Request) -> None:
    """FastAPI dependency: raise a structured 429 if the caller exceeds the window quota."""
    if os.environ.get("POCKET_MECHANICS_UNDER_TEST"):
        return

    now = time.time()
    key = _client_key(request)
    window_start, count = _buckets[key]

    # Start a fresh window if the previous one has elapsed.
    if now - window_start >= _WINDOW:
        _buckets[key] = [now, 1]
        return

    if count >= _REQUESTS:
        retry_after = max(1, int(_WINDOW - (now - window_start)))
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limited",
                "message": "Too many requests. Please slow down and try again shortly.",
                "retry_after_seconds": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )

    _buckets[key][1] = count + 1
