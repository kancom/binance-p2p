import abc
from typing import Optional

from p2p.application.domain.user import UserNotification

from ..foundation import UserInteractionEnum


class QueueRepo(metaclass=abc.ABCMeta):
    class NoAnswer(Exception):
        pass

    @abc.abstractmethod
    async def query(self, user_id: str, question: UserInteractionEnum) -> str:
        pass

    @abc.abstractmethod
    async def get_question(self, user_id: str) -> Optional[UserInteractionEnum]:
        pass

    @abc.abstractmethod
    async def get_notification(self, user_id: str) -> Optional[UserNotification]:
        pass

    @abc.abstractmethod
    async def put_answer(self, user_id: str, answer: str):
        pass

    @abc.abstractmethod
    async def put_notification(
        self,
        user_id: str,
        notification: UserInteractionEnum,
        arbitrary: Optional[str] = None,
    ):
        pass
