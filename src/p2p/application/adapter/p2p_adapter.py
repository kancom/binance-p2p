import abc
from decimal import Decimal
from typing import Tuple

from ..domain.common import Advertisement, Order, PeerOffer
from ..foundation import Currency, PaymentMethod


class P2PAdapter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def decode_balance_entry(self, entry: dict) -> Tuple[Currency, Decimal]:
        pass

    @abc.abstractmethod
    def decode_order_book_entry(self, entry: dict) -> Order:
        pass

    @abc.abstractmethod
    def decode_my_advertisment(self, entry: dict) -> Advertisement:
        pass

    @abc.abstractmethod
    def decode_ticker_entry(self, entry: dict) -> Tuple[Currency, Decimal]:
        pass

    @abc.abstractmethod
    def decode_peer_offer(self, entry: dict) -> PeerOffer:
        pass

    @abc.abstractmethod
    def decode_payment_methods(self, method: dict) -> dict:
        pass

    @abc.abstractmethod
    def serialize_ads_update(self, ads: Advertisement) -> dict:
        pass

    @abc.abstractmethod
    def serialize_ads_create(self, ads: Advertisement) -> dict:
        pass

    @abc.abstractmethod
    def serialize_ads_delete(self, ads: Advertisement) -> dict:
        pass

    @abc.abstractmethod
    def serialise_payment_method(self, method: PaymentMethod) -> dict:
        pass
