from decimal import Decimal


def test_decode_offer(peer_order):
    assert peer_order.amount == Decimal("57.3")
    assert peer_order.payment_methods == ["Papara"]
    assert peer_order.price == Decimal("17.45")
    assert peer_order.participants == ("binchanger", "vicky")
    assert peer_order.order_nb == 20382268565973348352
