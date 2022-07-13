import abc

from ..domain.bot import UserData


class UserDataRepo(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def save(self, data: UserData):
        pass

    @abc.abstractmethod
    async def get(self, user_id: str) -> UserData:
        pass
