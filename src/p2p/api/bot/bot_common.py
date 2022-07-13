from asyncio import Lock
from collections import defaultdict
from contextlib import asynccontextmanager
from enum import Enum
from typing import Dict

from aiogram.dispatcher.filters.state import State, StatesGroup
from dependency_injector.wiring import Provide, inject
from p2p.application import (AdsData, UserData, UserDataRepo, UserProfile,
                             UserSettings)
from p2p.wiring import Container as wiring

ABC = "abcdefghijklmnopqrstuvxyz"


def dict2str(values: dict) -> str:
    result = ""
    for letter, (k, v) in zip(ABC, values.items()):
        result += f"\n({letter}) {k}: {v}"
    return result + "\n"


class Buttons(str, Enum):
    # top level
    SETTINGS = "SETTINGS"
    PROFILE = "PROFILE"
    ADVERTISEMENTS = "ADVERTISEMENTS"
    OFFERS = "OFFERS"

    # Settings
    LANGUAGE = "LANGUAGE"
    SPREAD_COMP = "SPREAD_COMP"
    SPREAD = "SPREAD"
    INTERCEPTION = "INTERCEPTION"
    PAYMENT_COMMENT = "PAYMENT_COMMENT"

    # Profile
    LOGIN = "LOGIN"
    PASSWORD = "PASSWORD"
    NICK_NAME = "NICK_NAME"

    # Ads menu
    LIST = "LIST"
    NEW = "NEW"
    DELETE = "DELETE"

    # Ads properties
    DIRECTION = "DIRECTION"
    ASSET = "ASSET"
    FIAT = "FIAT"
    ASSET_AMOUNT = "ASSET_AMOUNT"
    PAYMENT_METHOD = "PAYMENT_METHOD"
    TIME_LIMIT = "TIME_LIMIT"
    MIN_ORDER = "MIN_AMOUNT"
    MAX_ORDER = "MAX_AMOUNT"


class StTopLevel(StatesGroup):
    default = State()


class StMainMenu(StatesGroup):
    ads = State()
    offers = State()


class StSettingsMain(StatesGroup):
    default = State()


class StSettings(StatesGroup):
    input = State()


class StSettingsLang(StatesGroup):
    default = State()


class StProfileMain(StatesGroup):
    default = State()


class StProfile(StatesGroup):
    input = State()


class StOffersMain(StatesGroup):
    default = State()


class StQuestion(StatesGroup):
    default = State()


class StNotification(StatesGroup):
    default = State()


class StAds(StatesGroup):
    default = State()
    input = State()
    list = State()
    delete = State()


class StAdsTyping(StatesGroup):
    default = State()


class StAdsChoosing(StatesGroup):
    default = State()


class Feature(str, Enum):
    lang = "lang"
    msgs2del = "msgs2del"
    question = "question"


@inject
async def get_userdata(
    user_id: str, userdata_repo: UserDataRepo = Provide[wiring.userdata_repo]
) -> UserData:
    ud = await userdata_repo.get(user_id)
    if ud is None:
        return UserData(
            user_id=user_id,
            settings=UserSettings(),
            profile=UserProfile(),
            ads=AdsData(),
        )
    return ud


@inject
async def save_userdata(
    user_data: UserData, userdata_repo: UserDataRepo = Provide[wiring.userdata_repo]
):
    await userdata_repo.save(user_data)


LOCKS: Dict[str, Lock] = defaultdict(Lock)


@asynccontextmanager
async def named_lock(name: str):
    lock = LOCKS[name]
    if lock.locked():
        raise ValueError("Already acquired")
    async with lock:
        yield
