from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel
from pydantic.fields import Field

from ..foundation import Currency, Direction, PaymentMethod


class Maker(BaseModel):
    user_no: str
    visible_name: str
    success_rate: Decimal
    orders_count: int
    is_profi: bool = False


class TradeEntity(BaseModel):
    offer_id: Optional[str]
    payment_methods: List[PaymentMethod]
    direction: Direction
    asset: Currency
    fiat: Currency
    price: Decimal


class TradeConditions(TradeEntity):
    initial_amount: Optional[Decimal]
    min_amount: Decimal
    max_amount: Decimal
    time_limit: Optional[int]
    digits: int = 2

    @property
    def init_amount_fiat(self):
        if self.initial_amount is not None:
            return self.initial_amount * self.price
        else:
            return self.max_amount * self.price

    @property
    def amount_spent(self):
        return self.init_amount_fiat - self.max_amount

    def volume_interception(self, o: "TradeConditions") -> int:
        left = max(self.min_amount, o.min_amount)
        right = min(self.max_amount, o.max_amount)
        own_len = self.max_amount - self.min_amount
        return int(100 * (right - left) / own_len)


class Order(TradeConditions):
    maker: Maker = Maker(
        user_no="0000", visible_name="self", success_rate=Decimal(1), orders_count=1
    )

    def __str__(self) -> str:
        return f"{self.direction}, {self.min_amount}-{self.max_amount}@{self.price} by {self.maker.visible_name}"


class Advertisement(TradeConditions):
    price_type: int = 1
    auto_reply: Optional[str] = ""
    floating_ratio: Optional[Decimal]
    remarks: Optional[str] = ""
    countries: List[str] = Field(default_factory=list)
    buyer_reg_age: int = 0


class PeerOffer(TradeEntity):
    order_nb: int
    amount: Decimal
    created: datetime
    participants: Tuple[str, str]


class Pair(BaseModel):
    asset: Currency
    fiat: Currency

    def __str__(self):
        return f"{self.asset}_{self.fiat}".upper()

    def __hash__(self) -> int:
        return hash((self.asset, self.fiat))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.__str__() == other.upper()
        if isinstance(other, Pair):
            return self.asset == other.asset and self.fiat == other.fiat
        return False


class CollectInfoResponse(BaseModel):
    best_ask: Order
    best_bid: Order
    sell_competitor: Order
    buy_competitor: Order


class ConvoyAdaptiveInterval(BaseModel):
    history: List[datetime]
    current: timedelta = timedelta(seconds=10)


INTERVAL_TRACKER: Dict[str, ConvoyAdaptiveInterval] = {}
