import abc
from enum import IntEnum
from typing import List, Optional

from ..adapter.p2p_adapter import P2PAdapter
from ..domain.common import Advertisement, Order, Pair, PeerOffer
from ..foundation import Currency, Direction, PaymentMethod


class P2POrderRepo(metaclass=abc.ABCMeta):
    class AuthFailed(Exception):
        pass

    class URL(IntEnum):
        ORDERBOOK = 1
        CREATE = 2
        UPDATE = 3
        DELETE = 4
        PAY_LIST = 5
        MY_ORDERS = 6  # my open orders - my ads
        MY_OFFERS = 7  # my pending orders - taker has accepted an order

    def __init__(self, adapter: P2PAdapter) -> None:
        self._adapter = adapter

    @abc.abstractmethod
    async def update_order(self, user_id: str, ads: Advertisement):
        pass

    @abc.abstractmethod
    async def place_order(self, user_id: str, ads: Advertisement):
        pass

    @abc.abstractmethod
    async def delete_order(self, user_id: str, ads_id: str):
        pass

    @abc.abstractmethod
    async def get_orderbook(
        self,
        pay_methods: List[PaymentMethod],
        asset: Currency,
        fiat: Currency,
        direction: Direction,
        rows: int = 20,
    ) -> List[Order]:
        pass

    # @abc.abstractmethod
    # async def get_order_history(
    #     self,
    #     user_id: str,
    #     asset: Optional[Currency],
    #     direction: Optional[Direction],
    #     from_ts: Optional[datetime],
    #     to_ts: Optional[datetime],
    #     status: Optional[OrderStatus],
    # ) -> List[Order]:
    #     pass

    @abc.abstractmethod
    async def get_payment_methods(self, user_id: str) -> List[str]:
        pass

    @abc.abstractmethod
    async def get_my_orders(
        self, user_id: str, pair: Optional[Pair] = None
    ) -> List[Advertisement]:
        pass

    @abc.abstractmethod
    async def get_my_offer(
        self, user_id: str, asset: Optional[Currency] = None
    ) -> List[PeerOffer]:
        pass
