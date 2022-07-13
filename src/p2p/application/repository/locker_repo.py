import abc
from typing import AsyncContextManager, Optional

from p2p.application import Exchange


class LockerRepo(metaclass=abc.ABCMeta):
    default_lock_name = "lock"

    @abc.abstractmethod
    async def get_lock(
        self, exchange: Exchange, name: Optional[str] = None, blocking: bool = True
    ) -> AsyncContextManager:
        pass
