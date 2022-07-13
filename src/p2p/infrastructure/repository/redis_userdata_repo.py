import json
from typing import Optional

import redis.asyncio as redis
from p2p.application import LockerRepo, UserData, UserDataRepo


class RedisUserDataRepo(UserDataRepo):
    key_mask = "bot_userdata_{suffix}"

    def __init__(self, redis_dsn: str, locker_repo: LockerRepo) -> None:
        self._redis = redis.from_url(redis_dsn, encoding="utf-8", decode_responses=True)
        self._locker_repo = locker_repo

    async def save(self, data: UserData):
        # lock is unnecessary. only one user per request
        key = self.key_mask.format(suffix=data.user_id)
        await self._redis.set(key, data.json())

    async def get(self, user_id: str) -> Optional[UserData]:
        key = self.key_mask.format(suffix=user_id)
        if await self._redis.exists(key):
            c = await self._redis.get(key)
            c = json.loads(c)
            return UserData(**c)
