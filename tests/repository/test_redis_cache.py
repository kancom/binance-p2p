
import pytest

from p2p.application import Currency, Direction, Exchange, Order
from p2p.infrastructure import RedisOrderBookCacheRepo


@pytest.fixture
def redis_docker_dsn():
    return "redis://localhost:5002"


@pytest.fixture
def repo(redis_docker_dsn):
    return RedisOrderBookCacheRepo(redis_dsn=redis_docker_dsn)


@pytest.mark.asyncio
async def test_cache(repo: RedisOrderBookCacheRepo):
    order = Order(
        payment_methods=["method"],
        direction=Direction.BUY,
        asset=Currency("some"),
        fiat=Currency("some"),
        price=100,
        min_amount=100,
        max_amount=1000,
    )
    orders = [order]
    await repo.put(Exchange.BINANCE, "some_some", orders=orders)
    orders_cached = await repo.read(Exchange.BINANCE, "some_some")
    assert orders == [Order(**o) for o in orders_cached]
