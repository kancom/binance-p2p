import abc
from decimal import Decimal
from enum import IntEnum
from typing import Dict

from p2p.application.foundation import Currency

from ..adapter.p2p_adapter import P2PAdapter


class PrivateDataRepo(metaclass=abc.ABCMeta):
    def __init__(self, adapter: P2PAdapter) -> None:
        self._adapter = adapter

    class URL(IntEnum):
        WALLET_FUNDING = 1

    @abc.abstractmethod
    def get_funding_balance(self) -> Dict[Currency, Decimal]:
        pass
