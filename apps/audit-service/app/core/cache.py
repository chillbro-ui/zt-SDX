import redis

from app.core.config import settings


rdb = redis.Redis(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT),
    decode_responses=True
)