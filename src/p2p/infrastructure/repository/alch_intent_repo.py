from typing import Dict, List, Optional, Tuple

from p2p.application import AdsFlow, IntentionRepo
from sqlalchemy import select

from .alchemy_models import IntentionModel
from .base import AsyncRepo


class AlchemyIntentionRepo(AsyncRepo, IntentionRepo):
    async def save(self, uuid: str, ads: Dict, settings: Dict):
        async with self._engine.begin() as conn:
            result = await conn.execute(
                IntentionModel.insert().values(
                    login=uuid, data={"ads": ads, "settings": settings}
                )
            )
            return result.lastrowid

    async def read_with_status(
        self, status: AdsFlow, uuid: Optional[str] = None
    ) -> List[Tuple[int, dict, dict]]:
        async with self._engine.begin() as conn:
            q = select(IntentionModel.c.intention_id, IntentionModel.c.data)
            if uuid is not None:
                q = q.where(IntentionModel.c.login == uuid)
            result = await conn.execute(q.where(IntentionModel.c.status == status))
            results = result.fetchall()
            if results is None:
                raise self.NotFound(f"Nothing found for {uuid}")
            return [
                (
                    result._mapping["intention_id"],
                    result._mapping["data"]["ads"],
                    result._mapping["data"]["settings"],
                )
                for result in results
            ]

    async def set_status(self, intention_id: int, value: AdsFlow):
        async with self._engine.begin() as conn:
            await conn.execute(
                IntentionModel.update()
                .values(status=value)
                .where(IntentionModel.c.intention_id == intention_id)
            )
