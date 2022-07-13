from datetime import datetime

from p2p.application import AuthRepo
from sqlalchemy import select

from .alchemy_models import AuthDataModel
from .base import AsyncRepo


class AlchemyAuthRepo(AsyncRepo, AuthRepo):
    async def save(self, uuid: str, auth_data: dict):
        async with self._engine.begin() as conn:
            result = await conn.execute(
                AuthDataModel.select().where(AuthDataModel.c.login == uuid)
            )
            result = result.fetchone()
            if result is None:
                result = await conn.execute(
                    AuthDataModel.insert().values(login=uuid, data=auth_data)
                )
            else:
                result = await conn.execute(
                    AuthDataModel.update()
                    .where(AuthDataModel.c.login == uuid)
                    .values(data=auth_data, updated_at=datetime.utcnow())
                )
            return result.lastrowid

    async def read(self, uuid: str) -> dict:
        async with self._engine.begin() as conn:
            result = await conn.execute(
                select(AuthDataModel.c.data).where(AuthDataModel.c.login == uuid)
            )
            result = result.scalar()
            if result is None:
                raise self.NotFound(f"user {uuid} not found")
            return result
