
import asyncio
import time

from app.core.config import (
    CACHE_SECONDS,
    MAX_CONCURRENT_REQUESTS,
)
from app.services.grid import to_grid
from app.services.weather import get_weather_data

_weather_cache = {}
_pending_tasks = {}

_semaphore = asyncio.Semaphore(
    MAX_CONCURRENT_REQUESTS
)


async def _fetch_weather(lat, lon, key):
    async with _semaphore:
        weather = await get_weather_data(lat, lon)

        _weather_cache[key] = {
            "data": weather,
            "expires_at": (
                time.monotonic() + CACHE_SECONDS
            ),
        }

        return weather


async def get_cached_weather(lat, lon):
    nx, ny = to_grid(lat, lon)
    key = (nx, ny)

    cached = _weather_cache.get(key)

    if cached:
        if cached["expires_at"] > time.monotonic():
            return cached["data"]

    # 동시에 같은 격자를 요청해도 한 번만 조회
    task = _pending_tasks.get(key)

    if task is None:
        task = asyncio.create_task(
            _fetch_weather(lat, lon, key)
        )
        _pending_tasks[key] = task

        def cleanup(finished_task):
            if _pending_tasks.get(key) is finished_task:
                _pending_tasks.pop(key, None)

            # 요청자가 취소되어도 예외가 방치되지 않도록 회수
            if not finished_task.cancelled():
                finished_task.exception()

        task.add_done_callback(cleanup)

    return await asyncio.shield(task)
