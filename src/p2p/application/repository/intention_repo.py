import abc
from typing import Dict, List, Optional, Tuple

from ..foundation import AdsFlow


class IntentionRepo(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def save(self, uuid: str, ads: Dict, settings: Dict):
        pass

    @abc.abstractmethod
    async def read_with_status(
        self, status: AdsFlow, uuid: Optional[str] = None
    ) -> List[Tuple[int, dict, dict]]:
        pass

    @abc.abstractmethod
    async def set_status(self, intention_id: int, value: AdsFlow):
        pass
