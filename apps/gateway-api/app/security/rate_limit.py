"""
Redis sliding window rate limiter.

Usage:
    check_rate_limit(request, key_prefix="login", limit=10, window=60)

Raises HTTP 429 if limit exceeded.
"""

import time

import redis
from fastapi import HTTPException, Request

from app.core.config import settings

_rdb = redis.Redis(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT),
    decode_responses=True,
)


def check_rate_limit(
    request: Request,
    key_prefix: str,
    limit: int,
    window: int,  # seconds
):
    """
    Sliding window rate limiter using Redis sorted sets.
    key_prefix: e.g. "login", "api"
    limit: max requests in window
    window: window size in seconds
    """
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate:{key_prefix}:{client_ip}"
    now = time.time()
    window_start = now - window

    pipe = _rdb.pipeline()
    # Remove entries outside the window
    pipe.zremrangebyscore(key, 0, window_start)
    # Add current request
    pipe.zadd(key, {str(now): now})
    # Count requests in window
    pipe.zcard(key)
    # Set TTL
    pipe.expire(key, window)
    results = pipe.execute()

    count = results[2]

    if count > limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {limit} requests per {window}s. Try again later.",
            headers={"Retry-After": str(window)},
        )
