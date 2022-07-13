import json
from datetime import datetime
from functools import partial
from math import ceil
from typing import Any, Dict, List, Optional, Tuple

import requests
from loguru import logger
from p2p.application import (Advertisement, AuthRepo, Direction, LockerRepo,
                             Order, P2PAdapter, P2POrderRepo, Pair,
                             PaymentMethod, PeerOffer, QueueRepo, User,
                             UserInteractionEnum, UserRepo)
from p2p.application.foundation import Currency, Exchange

from .bin_auth import BinanceAuthenticator


class BinanceP2PRepo(P2POrderRepo):
    BASE_URL = "https://p2p.binance.com/bapi/c2c/v2"
    URLS = {
        P2POrderRepo.URL.ORDERBOOK: ("POST", "friendly/c2c/adv/search"),
        P2POrderRepo.URL.UPDATE: ("POST", "private/c2c/adv/update"),
        P2POrderRepo.URL.CREATE: ("POST", "private/c2c/adv/publish"),
        P2POrderRepo.URL.PAY_LIST: (
            "POST",
            "private/c2c/pay-method/user-paymethods",
        ),
        P2POrderRepo.URL.MY_ORDERS: ("POST", "private/c2c/adv/list-by-page"),
        P2POrderRepo.URL.MY_OFFERS: ("POST", "private/c2c/order-match/order-list"),
        P2POrderRepo.URL.DELETE: ("POST", "private/c2c/adv/update-status"),
    }
    glob_headers = {
        "Accept": "*/*",
        "Host": "p2p.binance.com",
        "Accept-Encoding": "gzip, deflate, br",
        "content-type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0",
    }

    def __init__(
        self,
        adapter: P2PAdapter,
        auth_provider: BinanceAuthenticator,
        auth_repo: AuthRepo,
        user_repo: UserRepo,
        locker_repo: LockerRepo,
        user_question_repo: QueueRepo,
    ):
        super().__init__(adapter)
        self._session = requests.Session()
        self._session.headers.update(self.glob_headers)
        self._authenticator = auth_provider
        self._locker_repo = locker_repo
        self._user_repo = user_repo
        self._auth_repo = auth_repo
        self._notify_repo = user_question_repo
        self._user2auth_mapping: Dict[str, Tuple[datetime, Dict]] = {}

    async def get_payment_methods(self, user_id: str) -> List[str]:
        result = []
        headers = await self._add_auth_headers(user_id)
        headers.update({"Referer": "https://p2p.binance.com/en/postAd"})
        methods = await self._query(
            self.URL.PAY_LIST, user_id, data={}, headers=headers
        )
        for method in methods["data"]:
            self._adapter.decode_payment_methods(method)
            result.append(method["identifier"])
        return result

    async def _query(
        self,
        url_id: P2POrderRepo.URL,
        user_id: Optional[str] = None,
        headers: Optional[dict] = None,
        data: Optional[dict] = None,
        cookies: Optional[dict] = None,
    ):
        url = f"{self.BASE_URL}/{self.URLS[url_id][1]}"
        logger.info(url)
        lock = await self._locker_repo.get_lock(
            Exchange.BINANCE, name=user_id, blocking=True
        )
        async with lock:
            req_headers = {}
            if headers is not None and isinstance(headers, dict):
                req_headers.update(headers)

            if self.URLS[url_id][0] == "GET":
                method = partial(self._session.get, url, params=data, cookies=cookies)
            else:
                data = json.dumps(data, separators=(",", ":"))
                method = partial(self._session.post, url, data=data, cookies=cookies)
            resp = method(headers=req_headers)
            logger.debug(resp.status_code)
            if resp.status_code == requests.status_codes.codes.unauthorized:
                if user_id is not None:
                    user = await self._user_repo.get_by_presentation_id(user_id)
                    auth_lock = await self._locker_repo.get_lock(
                        Exchange.BINANCE, blocking=True
                    )
                    async with auth_lock:
                        auth_headers = await self._generate_headers(user)
                    req_headers.update(auth_headers)
                    resp = method(headers=req_headers)

            if (
                requests.status_codes.codes.multiple_choices < resp.status_code
                or resp.status_code < requests.status_codes.codes.ok
            ):
                raise ValueError(
                    f"unexpcted response {resp.status_code} {url}, {req_headers}, {data}, {resp.text}"
                )
            res = resp.json()
            if "success" in res and res["success"] != True:
                if "Ad remaining balance should not be less than 100" in res["message"]:
                    logger.warning(f"{res['message']} {data}")
                    return res
                if user_id is not None:
                    await self._notify_repo.put_notification(
                        user_id,
                        UserInteractionEnum.GENERIC_ERROR,
                        arbitrary=str(res["message"]),
                    )
                raise ValueError(f"{res['message']} {data}")
            return res

    async def get_orderbook(
        self,
        pay_methods: List[PaymentMethod],
        asset: Currency,
        fiat: Currency,
        direction: Direction,
        rows: int = 30,
    ) -> List[Order]:
        max_rows = 10
        pages = int(ceil(rows / max_rows))
        result = []
        for pg in range(pages):
            data = {
                "page": pg + 1,
                "rows": max_rows,
                "payTypes": [x for x in pay_methods],
                "countries": [],
                "publisherType": None,
                "asset": asset,
                "tradeType": direction.value,
                "fiat": fiat,
            }
            response = await self._query(P2POrderRepo.URL.ORDERBOOK, data=data)
            for ad in response["data"]:
                order = self._adapter.decode_order_book_entry(ad)
                result.append(order)
        return result[:rows]

    async def _add_auth_headers(self, user_id: str) -> Dict:
        user = await self._user_repo.get_by_presentation_id(user_id)
        try:
            auth_headers = await self._auth_repo.read(user.login)
        except:
            auth_headers = await self._generate_headers(user)
        return auth_headers

    async def _generate_headers(self, user: User) -> Dict:
        auth_headers = await self._authenticator.get_auth_headers(
            user.login, user.password
        )
        await self._auth_repo.save(user.login, auth_headers)
        return auth_headers

    async def update_order(self, user_id: str, ads: Advertisement):
        await self.get_payment_methods(user_id)
        data = self._adapter.serialize_ads_update(ads)
        headers = await self._add_auth_headers(user_id)
        headers.update(
            {"Referer": f"https://p2p.binance.com/en/advEdit?code={ads.offer_id}"}
        )
        await self._query(
            P2POrderRepo.URL.UPDATE, user_id=user_id, data=data, headers=headers
        )

    async def place_order(self, user_id: str, ads: Advertisement):
        await self.get_payment_methods(user_id)
        data = self._adapter.serialize_ads_create(ads)
        headers = await self._add_auth_headers(user_id)
        await self._query(
            P2POrderRepo.URL.CREATE, user_id=user_id, data=data, headers=headers
        )

    async def delete_order(self, user_id: str, ads_id: str):
        data = {"advNos": [ads_id], "advStatus": 4}
        headers = await self._add_auth_headers(user_id)
        headers.update({"Referer": "https://p2p.binance.com/en/myads"})
        await self._query(
            P2POrderRepo.URL.DELETE, user_id=user_id, data=data, headers=headers
        )

    async def get_my_offer(
        self, user_id: str, asset: Optional[Currency] = None
    ) -> List[PeerOffer]:
        headers = await self._add_auth_headers(user_id)
        data = {"page": 1, "rows": 10, "orderStatusList": [1, 2]}
        if asset is not None:
            data["asset"] = asset
        result = []
        ads = await self._query(
            P2POrderRepo.URL.MY_OFFERS, user_id=user_id, data=data, headers=headers
        )
        for ad in ads["data"]:
            result.append(self._adapter.decode_peer_offer(ad))
        return result

    async def get_my_orders(
        self, user_id: str, pair: Optional[Pair] = None
    ) -> List[Advertisement]:
        headers = await self._add_auth_headers(user_id)
        result = []
        data: Dict[str, Any] = {"inDeal": 1, "rows": 20, "page": 1, "advStatus": 1}
        if pair is not None:
            data["asset"] = pair.asset
        ads = await self._query(
            P2POrderRepo.URL.MY_ORDERS, user_id=user_id, data=data, headers=headers
        )
        for ad in ads["data"]:
            result.append(self._adapter.decode_my_advertisment(ad))
        return result
