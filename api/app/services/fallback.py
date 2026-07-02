import json
from collections.abc import Callable, Awaitable
from typing import Any
from redis.asyncio import Redis
from ..config import settings

CACHE_KEY = "hospitals:er_status"


async def get_with_fallback(
    redis: Redis,
    fetch_fn: Callable[[], Awaitable[Any]],
) -> tuple[Any, bool]:
    """캐시 hit 시 Redis 반환, miss 시 fetch 후 캐싱. (data, from_cache) 반환"""
    cached = await redis.get(CACHE_KEY)
    if cached:
        return json.loads(cached), True

    data = await fetch_fn()
    await redis.setex(CACHE_KEY, settings.REDIS_TTL, json.dumps(data, ensure_ascii=False))
    return data, False


async def set_cache(redis: Redis, data: list[dict]) -> None:
    await redis.setex(CACHE_KEY, settings.REDIS_TTL, json.dumps(data, ensure_ascii=False))
