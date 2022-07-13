import abc
from typing import List

from ..domain.common import Order, Pair
from ..foundation import Exchange


class OrderBookCacheRepo(metaclass=abc.ABCMeta):
    class NotFound(Exception):
        pass

    @abc.abstractmethod
    async def put(self, exchange: Exchange, pair: Pair, orders: List[Order]):
        pass

    @abc.abstractmethod
    async def read(self, exchange: Exchange, pair: Pair) -> List[dict]:
        pass
