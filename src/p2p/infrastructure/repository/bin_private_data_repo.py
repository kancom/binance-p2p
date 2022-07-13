import datetime as dt
import hashlib
import hmac
import json
from decimal import Decimal
from typing import Dict, Optional
from urllib.parse import urlencode

import requests
from p2p.application import Currency, P2PAdapter, PrivateDataRepo


class BinancePrivateDataRepo(PrivateDataRepo):
    BASE_URL = "http://api.binance.com"
    URLS = {
        PrivateDataRepo.URL.WALLET_FUNDING: (
            "POST",
            "sapi/v1/asset/get-funding-asset",
        ),
    }
    glob_headers = {
        "Accept": "*/*",
        "content-type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0",
    }

    def __init__(self, adapter: P2PAdapter, api_key: str, secret_key: str) -> None:
        super().__init__(adapter)
        self._session = requests.Session()
        self._api_key = api_key
        self._secret_key = secret_key
        self.glob_headers.update({"X-MBX-APIKEY": self._api_key})
        self._session.headers.update(self.glob_headers)

    def get_funding_balance(self) -> Dict[Currency, Decimal]:
        response = self._query(self.URL.WALLET_FUNDING)
        result = {}
        for line in response:
            symbol, balance = self._adapter.decode_balance_entry(line)
            result[symbol] = balance
        return result

    def _get_sign(self, data):
        m = hmac.new(
            self._secret_key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256
        )
        return m.hexdigest()

    @staticmethod
    def _get_timestamp() -> str:
        now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
        return str(round(now.timestamp() * 1000))

    def _query(
        self,
        url_id: PrivateDataRepo.URL,
        headers: Optional[dict] = None,
        data: Optional[dict] = None,
        cookies: Optional[dict] = None,
        signed: bool = True,
    ):
        url = f"{self.BASE_URL}/{self.URLS[url_id][1]}"
        if data is None:
            data = {}
        if signed:
            data["timestamp"] = self._get_timestamp()
            data["recvWindow"] = 10_000
            query_string = urlencode(data, True).replace("%40", "@")
            signature = self._get_sign(query_string)
            data["signature"] = signature

        req_headers = {}
        if headers is not None and isinstance(headers, dict):
            req_headers.update(headers)

        if self.URLS[url_id][0] == "GET":
            resp = self._session.get(
                url, params=data, headers=req_headers, cookies=cookies
            )
        else:
            # data = json.dumps(data, separators=(",", ":"))
            resp = self._session.post(
                url, params=data, headers=req_headers, cookies=cookies
            )
        if 300 < resp.status_code or resp.status_code < 200:
            raise ValueError(
                f"unexpcted response {resp.status_code} {url}, {req_headers}, {data}, {resp.text}"
            )
        return resp.json()
