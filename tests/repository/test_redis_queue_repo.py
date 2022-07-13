import asyncio

import pytest
from p2p.application import QueueRepo, UserInteractionEnum


@pytest.fixture
def user_id():
    return "vasia@ru.ru"


async def answering_maching(user_id, repo):
    while True:
        await asyncio.sleep(1)
        q = await repo.get_question(user_id)
        if q is not None:
            await repo.put_answer(user_id, "answer")
        else:
            break


@pytest.mark.asyncio
async def test_query(user_id, docker_redis_queue_repo: QueueRepo):
    a_t = answering_maching(user_id, docker_redis_queue_repo)
    q_t = docker_redis_queue_repo.query(user_id, UserInteractionEnum.ADS_PUBLISHED)
    l = await asyncio.gather(a_t, q_t)
    assert l == [None, "answer"]


# @pytest.mark.asyncio
# async def test_query1(user_id, docker_redis_queue_repo):
#     q_t = docker_redis_queue_repo.query(user_id, UserInteractionEnum.ASK_EMAIL_CODE)
#     l = await asyncio.gather(q_t)


@pytest.mark.asyncio
async def test_query2(user_id, docker_redis_queue_repo: QueueRepo):
    q_t = docker_redis_queue_repo.put_notification(
        user_id,
        notification=UserInteractionEnum.NEW_OFFER,
        arbitrary="Order some USDT TRY 100@10.23",
    )
    l = await asyncio.gather(q_t)
