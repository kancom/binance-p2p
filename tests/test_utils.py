from decimal import Decimal

from p2p.application import Currency, Direction, Order
from p2p.application.domain.common import CollectInfoResponse
from p2p.application.utils import calculate_price, get_comment


def test_get_comment():
    comment = "raz-c1\ndva - c2"
    method = "dva"
    assert "c2" == get_comment(comment, method)


def test_calculate_price():
    sell_c = Order(
        payment_methods=["method"],
        direction=Direction.SELL,
        asset=Currency("some"),
        fiat=Currency("some"),
        price=Decimal("63.73"),
        min_amount=100,
        max_amount=1000,
    )
    buy_c = Order(
        payment_methods=["method"],
        direction=Direction.BUY,
        asset=Currency("some"),
        fiat=Currency("some"),
        price=Decimal("63.50"),
        min_amount=100,
        max_amount=1000,
    )
    sell_b = Order(
        payment_methods=["method"],
        direction=Direction.SELL,
        asset=Currency("some"),
        fiat=Currency("some"),
        price=Decimal("63.70"),
        min_amount=100,
        max_amount=1000,
    )
    buy_b = Order(
        payment_methods=["method"],
        direction=Direction.BUY,
        asset=Currency("some"),
        fiat=Currency("some"),
        price=Decimal("63.53"),
        min_amount=100,
        max_amount=1000,
    )
    resp = CollectInfoResponse(
        my_buys=[],
        my_sells=[],
        best_bid=buy_b,
        best_ask=sell_b,
        sell_competitor=sell_c,
        buy_competitor=buy_c,
    )
    price = calculate_price(
        digits=2, direction=Direction.BUY, comp_spread=20, spread=15, info_resp=resp
    )
    assert price == Decimal("63.51")

    price = calculate_price(
        digits=2, direction=Direction.BUY, comp_spread=40, spread=15, info_resp=resp
    )
    assert price == Decimal("63.33")

    price = calculate_price(
        digits=2, direction=Direction.BUY, comp_spread=20, spread=30, info_resp=resp
    )
    assert price == Decimal("63.40")
