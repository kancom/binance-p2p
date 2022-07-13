from typing import List

from loguru import logger
from p2p.settings import AdsSettings

from ..domain.common import Advertisement, CollectInfoResponse, Order, Pair
from ..foundation import Direction, Exchange, PaymentMethod
from ..repository.orderbook_cache_repo import OrderBookCacheRepo
from ..repository.p2p_repo import P2POrderRepo
from ..utils import extract_info_from_orders


class CollectInfoUseCase:
    class NoCompetitiors(Exception):
        pass

    def __init__(
        self,
        p2p_repo: P2POrderRepo,
        ob_cache: OrderBookCacheRepo,
        exchange: Exchange,
    ) -> None:
        self._p2p_repo = p2p_repo
        self._ob_cache = ob_cache
        self._exchange = exchange
        self._logger = logger

    async def execute(
        self, ad: Advertisement, method: PaymentMethod, settings: AdsSettings
    ) -> CollectInfoResponse:
        pair = Pair(asset=ad.asset, fiat=ad.fiat)
        try:
            orderbook_raw: List[dict] = await self._ob_cache.read(self._exchange, pair)
            orderbook = [Order(**o) for o in orderbook_raw]

        except self._ob_cache.NotFound:
            orderbook = await self._p2p_repo.get_orderbook(
                pay_methods=[method],
                asset=pair.asset,
                fiat=pair.fiat,
                direction=Direction.SELL,
            )
            orderbook.extend(
                await self._p2p_repo.get_orderbook(
                    pay_methods=[method],
                    asset=pair.asset,
                    fiat=pair.fiat,
                    direction=Direction.BUY,
                )
            )
            await self._ob_cache.put(self._exchange, pair, orderbook)

        orders = {Direction.BUY: [], Direction.SELL: []}
        for o in orderbook:
            orders[o.direction].append(o)
        best_ask, sell_competitor = extract_info_from_orders(
            ad=ad,
            orders=orders[Direction.SELL],
            threshold=settings.interception_threshold,
            merchant=settings.merchant_name,
        )
        best_bid, buy_competitor = extract_info_from_orders(
            ad=ad,
            orders=orders[Direction.BUY],
            threshold=settings.interception_threshold,
            merchant=settings.merchant_name,
        )
        if sell_competitor is None or buy_competitor is None:
            logger.error(f"{sell_competitor}, {buy_competitor}")
            logger.warning(f"{len(orderbook)}")
            raise self.NoCompetitiors("Buy or Sell competitor wasn't found")
        return CollectInfoResponse(
            best_ask=best_ask,
            best_bid=best_bid,
            buy_competitor=buy_competitor,
            sell_competitor=sell_competitor,
        )
