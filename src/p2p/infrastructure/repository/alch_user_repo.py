from typing import Union

from p2p.application import User, UserRepo
from pydantic import EmailStr

from .alchemy_models import UserModel
from .base import AsyncRepo


class AlchemyUserRepo(AsyncRepo, UserRepo):
    async def get_by_presentation_id(self, presentation_id: Union[int, str]) -> User:
        async with self._engine.begin() as conn:
            result = await conn.execute(
                UserModel.select().where(UserModel.c.presentation_id == presentation_id)
            )
            result = result.fetchone()
            if result is None:
                raise self.NotFound(f"user {presentation_id} not found")
            return User(**result._mapping)

    async def get_by_login(self, login: EmailStr) -> User:
        async with self._engine.begin() as conn:
            result = await conn.execute(
                UserModel.select().where(UserModel.c.login == login)
            )
            result = result.fetchone()
            if result is None:
                raise self.NotFound(f"user {login} not found")
            return User(**result._mapping)

    async def save(self, user: User):
        async with self._engine.begin() as conn:
            result = await conn.execute(
                UserModel.select().where(UserModel.c.login == user.login)
            )
            result = result.fetchone()
            if result is not None:
                result = await conn.execute(
                    UserModel.update()
                    .where(UserModel.c.login == user.login)
                    .values(**user.dict())
                )
            else:
                result = await conn.execute(UserModel.insert().values(**user.dict()))
