import copy
from decimal import Decimal
from typing import Dict

from p2p.application.foundation import Currency
from p2p.settings import Settings

from ..domain.common import Pair
from ..repository.market_repo import MarketDataRepo
from ..repository.private_data_repo import PrivateDataRepo


class GetBalanceUseCase:
    PIVOT_SYMBOL = "USDT"

    def __init__(
        self,
        settings: Settings,
        market_repo: MarketDataRepo,
        private_data_repo: PrivateDataRepo,
    ) -> None:
        self._settings = settings
        self._market_repo = market_repo
        self._private_repo = private_data_repo
        self._pairs = [
            Pair(asset=k.split("_")[0], fiat=k.split("_")[1])
            for k in self._settings.amount_dict.keys()
        ]

    def execute(self) -> Dict[Currency, Decimal]:
        balances_raw = self._private_repo.get_funding_balance()
        balances_usdt = {}
        ticker_pairs = copy.deepcopy(self._pairs)
        for asset, balance in balances_raw.items():
            if asset == self.PIVOT_SYMBOL:
                balances_usdt[asset] = balance
            elif asset in self._settings.fiat_assets:
                pair = Pair(asset=self.PIVOT_SYMBOL, fiat=asset)
                ticker_pairs.append(pair)
            else:
                pair = Pair(fiat=self.PIVOT_SYMBOL, asset=asset)
                ticker_pairs.append(pair)

        ticker_pairs = list(set(ticker_pairs))
        tickers = self._market_repo.get_ticker(ticker_pairs)
        for asset, balance in balances_raw.items():
            if asset == self.PIVOT_SYMBOL:
                balances_usdt[asset] = balance
            elif asset in self._settings.fiat_assets:
                pair = Pair(asset=self.PIVOT_SYMBOL, fiat=asset)
                balances_usdt[asset] = balance / tickers[pair]
            else:
                pair = Pair(fiat=self.PIVOT_SYMBOL, asset=asset)
                balances_usdt[asset] = balance * tickers[pair]
        return balances_usdt
