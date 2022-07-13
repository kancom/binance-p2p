import json

import pytest
from p2p.infrastructure import (BinP2PAdapter, RedisOrderBookCacheRepo,
                                RedisQueueRepo)


@pytest.fixture
def peer_order():
    with open("tests/bin_offer.json", "r") as f:
        offer_json = f.read()
    offer_dict = json.loads(offer_json)
    adapter = BinP2PAdapter()
    result = adapter.decode_peer_offer(offer_dict["data"][0])
    return result


@pytest.fixture
def redis_docker_dsn():
    return "redis://localhost:5002"


@pytest.fixture
def docker_redis_queue_repo(redis_docker_dsn):
    orderbook_cache_repo = RedisOrderBookCacheRepo(redis_dsn=redis_docker_dsn)
    return RedisQueueRepo(locker_repo=orderbook_cache_repo, redis_dsn=redis_docker_dsn)
