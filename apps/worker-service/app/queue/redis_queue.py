import json
from typing import cast

import redis

from app.core.config import settings


client = redis.Redis(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT),
    decode_responses=True,
)

QUEUE_NAME = "file_jobs"


def enqueue(job: dict):
    client.rpush(
        QUEUE_NAME,
        json.dumps(job),
    )


def dequeue():
    item = client.lpop(QUEUE_NAME)

    if item is None:
        return None

    payload = cast(str, item)

    return json.loads(payload)