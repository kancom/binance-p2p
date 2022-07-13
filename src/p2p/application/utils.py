from decimal import Decimal
from typing import List, Tuple

from .domain.common import Advertisement, CollectInfoResponse, Order
from .foundation import Direction


def extract_info_from_orders(
    orders: List[Order],
    ad: Advertisement,
    threshold: int,
    merchant: str,
) -> Tuple[Order, Order]:
    """Get best price and competitor"""
    foreign_orders = [o for o in orders if o.maker.visible_name != merchant]
    best_price = foreign_orders[0]
    competitors = [o for o in foreign_orders if ad.volume_interception(o) > threshold]
    if len(competitors) == 0:
        competitors = [best_price]

    return best_price, competitors[0]


def calculate_price(
    direction: Direction,
    comp_spread: int,
    spread: int,
    digits: int,
    info_resp: CollectInfoResponse,
) -> Decimal:
    step = Decimal(10 ** (-digits)).quantize(Decimal("1.0000"))
    if direction == Direction.SELL:
        price = info_resp.sell_competitor.price - step
        price = max(price, info_resp.buy_competitor.price + comp_spread * step)
        price = max(price, info_resp.best_bid.price + spread * step)
    elif direction == Direction.BUY:
        price = info_resp.buy_competitor.price + step
        price = min(price, info_resp.sell_competitor.price - comp_spread * step)
        price = min(price, info_resp.best_ask.price - spread * step)
    return price


def get_comment(comments: str, method: str) -> str:
    result = ""
    try:
        for line in comments.split("\n"):
            m, c = line.split("-")
            m = m.strip()
            c = c.strip()
            if method == m:
                result = c
                break
    finally:
        return result
