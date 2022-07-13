import asyncio
import json
from typing import AsyncContextManager, Optional

import redis.asyncio as redis
from loguru import logger
from p2p.application import (Exchange, LockerRepo, QueueRepo,
                             UserInteractionEnum, UserNotification,
                             UserQuestion)


class RedisQueueRepo(QueueRepo):
    question_lock_name: str = "msg_lock"
    question_queue_name: str = "msg_queue"
    notification_lock_name: str = "notify_lock"
    notification_queue_name: str = "notify_queue"
    poll_interval: int = 1

    def __init__(self, redis_dsn: str, locker_repo: LockerRepo) -> None:
        self._redis = redis.from_url(redis_dsn, encoding="utf-8", decode_responses=True)
        self._locker_repo = locker_repo

    async def _get_lock(self, name: str) -> AsyncContextManager:
        return await self._locker_repo.get_lock(
            exchange=Exchange.UNSPECIFIED, name=name
        )

    async def put_notification(
        self,
        user_id: str,
        notification: UserInteractionEnum,
        arbitrary: Optional[str] = None,
    ):
        lock = await self._get_lock(self.notification_lock_name)
        async with lock:
            llen = await self._redis.llen(self.notification_queue_name)
            logger.debug(f"There are {llen} notofications")
            c = UserNotification(
                user_id=user_id, notification=notification, arbitrary=arbitrary
            )
            await self._redis.rpush(self.notification_queue_name, c.json())

    async def get_notification(self, user_id: str) -> Optional[UserNotification]:
        lock = await self._get_lock(self.notification_lock_name)
        async with lock:
            llen = await self._redis.llen(self.notification_queue_name)
            for _ in range(llen):
                c = await self._redis.lpop(self.notification_queue_name)
                c = json.loads(c)
                try:
                    candidate = UserNotification(**c)
                except:
                    logger.error(c)
                    raise
                if str(candidate.user_id) == str(user_id):
                    logger.debug(f"{user_id} {candidate.notification}")
                    return candidate
                await self._redis.rpush(self.notification_queue_name, json.dumps(c))

    async def put_answer(self, user_id: str, answer: str):
        lock = await self._get_lock(self.question_lock_name)
        async with lock:
            llen = await self._redis.llen(self.question_queue_name)
            logger.debug(f"There are {llen} questions")
            for _ in range(llen):
                c = await self._redis.lpop(self.question_queue_name)
                c = json.loads(c)
                candidate = UserQuestion(**c)
                if candidate.answer is None and str(candidate.user_id) == str(user_id):
                    candidate.answer = answer
                    logger.debug(f"{user_id} {answer}")
                    await self._redis.rpush(
                        self.question_queue_name, json.dumps(candidate.dict())
                    )
                    break
                await self._redis.rpush(self.question_queue_name, json.dumps(c))

    async def get_question(self, user_id: str) -> Optional[UserInteractionEnum]:
        lock = await self._get_lock(self.question_lock_name)
        async with lock:
            llen = await self._redis.llen(self.question_queue_name)
            for _ in range(llen):
                c = await self._redis.lpop(self.question_queue_name)
                await self._redis.rpush(self.question_queue_name, c)
                c = json.loads(c)
                candidate = UserQuestion(**c)
                if candidate.answer is None and str(candidate.user_id) == str(user_id):
                    logger.debug(f"{user_id} {candidate.question}")
                    return candidate.question

    async def query(self, user_id: str, question: UserInteractionEnum) -> str:
        lock = await self._get_lock(self.question_lock_name)
        # await self._redis.delete(self.lock_name)
        async with lock:
            llen = await self._redis.llen(self.question_queue_name)
            for _ in range(llen):
                c = await self._redis.lpop(self.question_queue_name)
                c = json.loads(c)
                candidate = UserQuestion(**c)
                if candidate.answer is not None and str(candidate.user_id) == str(
                    user_id
                ):
                    logger.info(f"consume old question {c}")
        q = UserQuestion(user_id=user_id, question=question)
        await self._redis.rpush(self.question_queue_name, json.dumps(q.dict()))
        logger.debug(f"{user_id} question put")
        for _ in range(600):
            await asyncio.sleep(self.poll_interval)
            async with lock:
                llen = await self._redis.llen(self.question_queue_name)
                for _ in range(llen):
                    c = await self._redis.lpop(self.question_queue_name)
                    c = json.loads(c)
                    candidate = UserQuestion(**c)
                    if candidate.answer is not None and candidate.user_id == user_id:
                        logger.debug(f"{user_id} answer received")
                        return candidate.answer
                    await self._redis.rpush(self.question_queue_name, json.dumps(c))
        raise self.NoAnswer(f"No answer from user {user_id}")
