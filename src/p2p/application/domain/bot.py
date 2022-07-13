from typing import Literal, Optional

from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    language: Literal["en", "ru", ""] = ""
    spread_comp: int = Field(
        default=10, description="Spread against opposite competitor"
    )
    spread: int = Field(default=10, description="Spread against best opposite price")
    interception: int = Field(
        default=50,
        description="Integer percents of volume interception to consider as a competitor",
    )
    payment_comment: Optional[str] = Field(
        default=None,
        description="Auto reply/post on behalf on the user for specific payment method",
    )


class UserProfile(BaseModel):
    login: Optional[str] = Field(description="platform login", default=None)
    password: Optional[str] = Field(description="platform password", default=None)
    nick_name: Optional[str] = Field(description="platform nickname", default=None)

    @property
    def is_complete(self):
        return (
            self.login is not None
            and self.password is not None
            and self.nick_name is not None
        )


class AdsData(BaseModel):
    direction: Optional[Literal["buy", "sell"]] = Field(
        description="platform nickname", default=None
    )
    asset: Optional[str] = None
    fiat: Optional[str] = None
    payment_method: Optional[str] = None
    asset_amount: Optional[int] = None
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None
    time_limit: Optional[int] = None


class UserData(BaseModel):
    user_id: str
    settings: UserSettings
    profile: UserProfile
    ads: AdsData
    flex: dict = Field(default_factory=dict, description="for any arbitrary usage")
