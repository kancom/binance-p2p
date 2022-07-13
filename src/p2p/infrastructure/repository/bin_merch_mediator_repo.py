import asyncio
from datetime import datetime, timedelta
from typing import Iterable, List

import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from p2p.application import MerchMediatorRepo

sec = timedelta(seconds=1)


# def time_m(func):
#     async def wrapped(*args, **kwargs):
#         ts = time.monotonic()
#         res = None
#         try:
#             res = await func(*args, **kwargs)
#         finally:
#             logger.debug(time.monotonic() - ts)
#         return res

#     return wrapped


async def backgroud_query(
    url: str, method: str = "get", params: dict = None, headers: dict = None
):
    async with aiohttp.ClientSession() as session:
        _method = getattr(session, method)
        kwargs = {"headers": headers}
        if method in ("delete", "get"):
            kwargs["params"] = params
        elif method == "post":
            kwargs["json"] = params
        logger.debug(f"{_method} {url} {kwargs}")
        await _method(url, **kwargs)
        logger.debug("done")


class BinanceMerchMediatorRepo(MerchMediatorRepo):
    ASSETS = ("BTC", "USDT", "BUSD", "BNB", "ETH", "SHIB")

    def __init__(self, api_url: str, timeout: int = 8) -> None:
        self._api_url = api_url
        self._scheduler = AsyncIOScheduler()
        self._scheduler.start()
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    def time_limit(self) -> Iterable[str]:
        return tuple(map(str, (15, 30, 45, 60, 120, 180)))

    def asset(self) -> Iterable[str]:
        return self.ASSETS

    async def pay_method(self, user_id: str) -> Iterable[str]:
        url = f"{self._api_url}/pay-methods"
        parameters = {"user_id": user_id}
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            try:
                response = await session.get(url, params=parameters)
            except asyncio.exceptions.TimeoutError:
                self._scheduler.add_job(
                    backgroud_query,
                    kwargs={"url": url, "params": parameters},
                    run_date=datetime.utcnow() + sec,
                )
                raise self.TimeOut("Auth required")
            if response.status > 299:
                text = await response.text()
                raise Exception(
                    f"Response {response.status}, {response.headers}, {text}"
                )
            return await response.json()

    async def my_ads(self, user_id: str) -> List[dict]:
        url = f"{self._api_url}/my-ads"
        parameters = {"user_id": user_id}
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            try:
                response = await session.get(url, params=parameters)
            except asyncio.exceptions.TimeoutError:
                self._scheduler.add_job(
                    backgroud_query,
                    kwargs={"url": url, "params": parameters},
                    run_date=datetime.utcnow() + sec,
                )
                raise self.TimeOut("Auth required")
            if response.status > 299:
                text = await response.text()
                raise Exception(
                    f"Response {response.status}, {response.headers}, {text}"
                )
            return await response.json()

    async def delete_ads(self, user_id: str, ads_id: str):
        url = f"{self._api_url}/my-ads"
        parameters = {"user_id": user_id, "ads_id": ads_id}
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            try:
                response = await session.delete(url, params=parameters)
            except asyncio.exceptions.TimeoutError:
                self._scheduler.add_job(
                    backgroud_query,
                    kwargs={"url": url, "method": "delete", "params": parameters},
                    run_date=datetime.utcnow() + sec,
                )
                raise self.TimeOut("Auth required")
            if response.status > 299:
                text = await response.text()
                raise Exception(
                    f"Response {response.status}, {response.headers}, {text}"
                )
            return await response.json()

    async def post_ads(self, user_id: str, ads: dict, settings: dict):
        url = f"{self._api_url}/my-ads"
        parameters = {"user_id": user_id, "ads": ads, "settings": settings}
        headers = {"content-type": "application/json"}
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            try:
                response = await session.post(url, json=parameters, headers=headers)
            except asyncio.exceptions.TimeoutError:
                self._scheduler.add_job(
                    backgroud_query,
                    kwargs={"url": url, "method": "post", "params": parameters},
                    run_date=datetime.utcnow() + sec,
                )
                raise self.TimeOut("Auth required")
            if response.status > 299:
                text = await response.text()
                raise Exception(
                    f"Response {response.status}, {response.headers}, {text}"
                )
            return await response.json()

    async def my_offers(self, user_id: str) -> List[dict]:
        url = f"{self._api_url}/my-offers"
        parameters = {"user_id": user_id}
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            try:
                response = await session.get(url, params=parameters)
            except asyncio.exceptions.TimeoutError:
                self._scheduler.add_job(
                    backgroud_query,
                    kwargs={"url": url, "params": parameters},
                    run_date=datetime.utcnow() + sec,
                )
                raise self.TimeOut("Auth required")
            if response.status > 299:
                text = await response.text()
                raise Exception(
                    f"Response {response.status}, {response.headers}, {text}"
                )
            return await response.json()
