from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, EmailStr

from ..foundation import UserInteractionEnum


class User(BaseModel):
    login: EmailStr
    password: str
    nick_name: str
    active_until: datetime = datetime.utcnow()
    registered_at: datetime = datetime.utcnow()
    presentation_id: Union[int, str]

    @property
    def is_active(self):
        return datetime.utcnow() < self.active_until


class UserQuestion(BaseModel):
    user_id: str
    question: UserInteractionEnum
    answer: Optional[str]


class UserNotification(BaseModel):
    user_id: str
    notification: UserInteractionEnum
    arbitrary: Optional[str]
