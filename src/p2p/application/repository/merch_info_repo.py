import abc
from typing import Iterable, List


class MerchMediatorRepo(metaclass=abc.ABCMeta):
    class TimeOut(Exception):
        pass

    def direction(self) -> Iterable[str]:
        return "buy", "sell"

    @abc.abstractmethod
    def asset(self) -> Iterable[str]:
        pass

    @abc.abstractmethod
    async def pay_method(self, user_id: str) -> Iterable[str]:
        pass

    @abc.abstractmethod
    def time_limit(self) -> Iterable[str]:
        pass

    @abc.abstractmethod
    async def my_ads(self, user_id: str) -> List[dict]:
        pass

    @abc.abstractmethod
    async def delete_ads(self, user_id: str, ads_id: str):
        pass

    @abc.abstractmethod
    async def post_ads(self, user_id: str, ads: dict, settings: dict):
        pass

    @abc.abstractmethod
    async def my_offers(self, user_id: str) -> List[dict]:
        pass
