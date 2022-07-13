import abc

from p2p.application import Exchange


class IncrementRepo(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def update(self, exchange: Exchange, name: str, value: str) -> bool:
        pass
