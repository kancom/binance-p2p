import abc
from typing import Union

from pydantic import EmailStr

from ..domain.user import User


class UserRepo(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def get_by_presentation_id(self, presentation_id: Union[int, str]) -> User:
        pass

    @abc.abstractmethod
    async def get_by_login(self, login: EmailStr) -> User:
        pass

    @abc.abstractmethod
    async def save(self, user: User):
        pass
