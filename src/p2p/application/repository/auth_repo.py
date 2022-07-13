import abc


class AuthRepo(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def save(self, uuid: str, auth_data: dict):
        pass

    @abc.abstractmethod
    async def read(self, uuid: str) -> dict:
        pass
