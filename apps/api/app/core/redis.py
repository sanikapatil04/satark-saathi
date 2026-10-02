import redis.asyncio as aioredis
from typing import AsyncGenerator
from app.core.config import settings

redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    yield redis_client
