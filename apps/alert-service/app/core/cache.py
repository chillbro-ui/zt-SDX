import os
import redis

# Redis connection for alert-service (optional — not currently used)
_host = os.getenv("REDIS_HOST", "redis")
_port = int(os.getenv("REDIS_PORT", "6379"))

rdb = redis.Redis(host=_host, port=_port, decode_responses=True)
