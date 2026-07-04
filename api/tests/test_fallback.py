import json
from unittest.mock import AsyncMock

import pytest

from app.services.fallback import get_with_fallback, CACHE_KEY


@pytest.mark.asyncio
async def test_cache_hit_returns_cached_data_without_calling_fetch_fn():
    cached_items = [{"hpid": "A001", "hvec": 3}]
    redis = AsyncMock()
    redis.get.return_value = json.dumps(cached_items, ensure_ascii=False)
    fetch_fn = AsyncMock()

    data, from_cache = await get_with_fallback(redis, fetch_fn)

    assert data == cached_items
    assert from_cache is True
    fetch_fn.assert_not_called()
    redis.setex.assert_not_called()


@pytest.mark.asyncio
async def test_cache_miss_calls_fetch_fn_and_caches_result():
    fresh_items = [{"hpid": "A002", "hvec": 1}]
    redis = AsyncMock()
    redis.get.return_value = None
    fetch_fn = AsyncMock(return_value=fresh_items)

    data, from_cache = await get_with_fallback(redis, fetch_fn)

    assert data == fresh_items
    assert from_cache is False
    fetch_fn.assert_called_once()
    redis.setex.assert_called_once()

    args, _ = redis.setex.call_args
    assert args[0] == CACHE_KEY
    assert json.loads(args[2]) == fresh_items