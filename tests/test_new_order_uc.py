import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from p2p.application import (CheckNewOffersUseCase, IncrementRepo,
                             IntentionRepo, P2POrderRepo, PeerOffer)


@pytest.fixture
def user_id():
    return "some"


@pytest.fixture
def intents(user_id):
    return [(1, {}, {"user_id": user_id})]


@pytest.fixture
def intent_repo(intents):
    repo = MagicMock(IntentionRepo)
    repo.read_with_status = AsyncMock(return_value=intents)
    return repo


@pytest.fixture
def p2p_repo(peer_order):
    repo = MagicMock(P2POrderRepo)
    repo.get_my_offer = AsyncMock(return_value=[peer_order])
    return repo


async def answering_maching(user_id, repo):
    for _ in range(5):
        await asyncio.sleep(1)
        q = await repo.get_notification(user_id)
        if q is not None:
            return True
    return False


@pytest.mark.asyncio
async def test_new_order(intent_repo, p2p_repo, docker_redis_queue_repo, user_id):
    inc_repo = AsyncMock(IncrementRepo)
    inc_repo.update.return_value = True
    uc = CheckNewOffersUseCase(
        p2p_repo=p2p_repo,
        notification_repo=docker_redis_queue_repo,
        intent_repo=intent_repo,
        inc_repo=inc_repo,
    )
    e = uc.execute()
    am = answering_maching(user_id, docker_redis_queue_repo)
    _, am_res = await asyncio.gather(e, am)
    assert am_res == True
