import json
from typing import AsyncContextManager, List, Optional

import redis.asyncio as redis
from p2p.application import (Exchange, IncrementRepo, LockerRepo, Order,
                             OrderBookCacheRepo, Pair)

LOCKS = {}


class RedisOrderBookCacheRepo(OrderBookCacheRepo, IncrementRepo, LockerRepo):
    poll_interval: int = 1

    def __init__(self, redis_dsn: str, ttl: int = 10) -> None:
        self._redis = redis.from_url(redis_dsn, encoding="utf-8", decode_responses=True)
        self._ttl = ttl

    @staticmethod
    def _get_key(exchange: Exchange, pair: Pair):
        return f"{exchange.value}:{str(pair)}"

    async def put(self, exchange: Exchange, pair: Pair, orders: List[Order]):
        key = self._get_key(exchange, pair)
        prepared = [o.json() for o in orders]
        value = json.dumps(prepared)
        await self._redis.set(key, value, self._ttl)

    async def read(self, exchange: Exchange, pair: Pair) -> List[dict]:
        key = self._get_key(exchange, pair)
        raw = await self._redis.get(key)
        if raw is None:
            raise self.NotFound(f"key {key} wasn't found")
        raw = json.loads(raw)
        if isinstance(raw, list):
            raw = [json.loads(r) for r in raw]
        return raw

    async def update(self, exchange: Exchange, name: str, value: str) -> bool:
        key = f"{exchange.value}_{name}_incremental"
        if await self._redis.exists(key):
            old_val = await self._redis.get(key)
            if old_val == value:
                return False
        await self._redis.set(key, value)
        return True

    async def get_lock(
        self, exchange: Exchange, name: Optional[str] = None, blocking: bool = True
    ) -> AsyncContextManager:
        lock_name = (
            f"{exchange.value}_{name}"
            if name is not None
            else f"{exchange.value}_{self.default_lock_name}"
        )
        expire = await self._redis.ttl(lock_name)
        if expire == -1:
            await self._redis.delete(lock_name)
        lock = LOCKS.get(lock_name, None)
        if lock is None:
            lock = self._redis.lock(
                lock_name,
                timeout=300.0,
                blocking_timeout=1.0 if blocking else None,
                thread_local=False,
            )
            LOCKS[lock_name] = lock
        return lock
