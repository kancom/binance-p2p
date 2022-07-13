import json
from decimal import Decimal
from typing import Dict, List, Optional

import requests
from p2p.application import MarketDataRepo, P2PAdapter, Pair


class BinanceMarketDataRepo(MarketDataRepo):
    BASE_URL = "https://api.binance.com"
    URLS = {
        MarketDataRepo.URL.TICKER: ("GET", "api/v3/ticker/price"),
    }
    glob_headers = {
        "Accept": "*/*",
        "content-type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0",
    }

    def __init__(self, adapter: P2PAdapter) -> None:
        super().__init__(adapter)
        self._session = requests.Session()

    def get_ticker(self, symbols: List[Pair]) -> Dict[Pair, Decimal]:
        reverse_map = {str(s).replace("_", ""): s for s in symbols}
        if len(symbols) == 1:
            data = {"symbol": str(symbols[0]).replace("_", "")}
        else:
            data = {
                "symbols": str(list(reverse_map.keys()))
                .replace("'", '"')
                .replace(" ", "")
            }
        response = self._query(self.URL.TICKER, data=data)
        result = {}
        if isinstance(response, dict):
            response = [response]
        for ticker in response:
            symbol, price = self._adapter.decode_ticker_entry(ticker)
            result[reverse_map[symbol]] = price
        return result

    def _query(
        self,
        url_id: MarketDataRepo.URL,
        headers: Optional[dict] = None,
        data: Optional[dict] = None,
        cookies: Optional[dict] = None,
    ):
        url = f"{self.BASE_URL}/{self.URLS[url_id][1]}"
        req_headers = {}
        if headers is not None and isinstance(headers, dict):
            req_headers.update(headers)

        if self.URLS[url_id][0] == "GET":
            resp = self._session.get(
                url, params=data, headers=req_headers, cookies=cookies
            )
        else:
            resp = self._session.post(
                url, data=data, headers=req_headers, cookies=cookies
            )
        if 300 < resp.status_code or resp.status_code < 200:
            raise ValueError(
                f"unexpcted response {resp.status_code} {url}, {req_headers}, {data}, {resp.text}"
            )
        return resp.json()
