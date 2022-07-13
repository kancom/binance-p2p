import abc
from decimal import Decimal
from enum import IntEnum
from typing import Dict, List

from ..adapter.p2p_adapter import P2PAdapter
from ..domain.common import Pair


class MarketDataRepo(metaclass=abc.ABCMeta):
    def __init__(self, adapter: P2PAdapter) -> None:
        self._adapter = adapter

    class URL(IntEnum):
        TICKER = 1

    @abc.abstractmethod
    def get_ticker(self, symbols: List[Pair]) -> Dict[Pair, Decimal]:
        pass
