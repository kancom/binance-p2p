import json
from unittest.mock import AsyncMock

import pytest
from p2p.application import (CollectInfoUseCase, Exchange, OrderBookCacheRepo,
                             Pair)
from p2p.infrastructure import BinP2PAdapter
from p2p.settings import AdsSettings


async def get_orderbook(*args, **kwargs):
    adapter = BinP2PAdapter()
    result = []
    with open("tests/orderbook.json", "r") as f:
        js = f.read()
    response = json.loads(js)
    for ad in response["data"]:
        order = adapter.decode_order_book_entry(ad)
        result.append(order)
    return result


@pytest.mark.asyncio
async def test_collect_info():
    user_id = "some"
    pair = Pair(asset="USDT", fiat="RUB")
    p2p_repo = AsyncMock()
    p2p_repo.get_my_orders.return_value = []
    p2p_repo.get_orderbook.side_effect = get_orderbook
    ob_cache = AsyncMock()
    ob_cache.NotFound = OrderBookCacheRepo.NotFound
    ob_cache.read.side_effect = OrderBookCacheRepo.NotFound
    uc = CollectInfoUseCase(
        p2p_repo=p2p_repo, ob_cache=ob_cache, exchange=Exchange.BINANCE
    )
    await uc.execute(
        user_id=user_id, pair=pair, method=["TinkoffNew"], settings=AdsSettings()
    )
