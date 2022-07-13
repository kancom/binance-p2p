from decimal import Decimal
from enum import Enum, IntEnum, auto
from typing import Dict

from pydantic.types import constr

# class PaymentMethod(str, Enum):
#     TINKOFF = "Tinkoff"
#     ROSBANK = "RosBank"
#     RUBFIATBALANCE = "RUBfiatbalance"
#     UAHFIATBALANCE = "UAHfiatbalance"
#     POSTBANKRUSSIA = "PostBankRussia"
#     ABANK = "ABank"
#     ADVCASH = "Advcash"
#     HOMECREDITBANK = "HomeCreditBank"
#     MOBILETOPUP = "Mobiletopup"
#     PAYEER = "Payeer"
#     QIWI = "QIWI"
#     RAIFFEISENBANKRUSSIA = "RaiffeisenBankRussia"
#     YANDEXMONEY = "YandexMoney"
#     MTSBANK = "MTSBank"
#     BANK = "BANK"
#     BCSBANK = "BCSBank"
#     RUSSIANSTANDARDBANK = "RussianStandardBank"
#     RENAISSANCECREDIT = "RenaissanceCredit"
#     URALSIBBANK = "UralsibBank"
#     UNICREDITRUSSIA = "UniCreditRussia"
#     OTPBANKRUSSIA = "OTPBankRussia"
#     KUVEYTTURK = "KuveytTurk"
#     Papara = "Papara"


class Exchange(str, Enum):
    UNSPECIFIED = "UNSPECIFIED"
    BINANCE = "Binance"


class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(IntEnum):
    NEW = 1
    CANCELLED = auto()
    PAID = auto()
    COMPLETED = auto()


class UserAction(IntEnum):
    SINGLE_ORDER = 1
    OPPOSITE_ORDERS = 2


class AdsFlow(IntEnum):
    NEW = 1
    PLACED = 2
    FAILED = 3
    IDLE = 4
    CONVOYING = 5
    COMPLETED = 6


class UserInteractionEnum(str, Enum):
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_FAILED = "AUTH_FAILED"
    AUTHENTICATED = "AUTHENTICATED"

    ASK_EMAIL_CODE = "ASK_EMAIL_CODE"
    ASK_PHONE_CODE = "ASK_PHONE_CODE"
    ASK_AUTH_CODE = "ASK_AUTH_CODE"
    ASK_CHOICE = "ASK_CHOICE"

    SECTION_START = "SECTION_START"
    SECTION_SETTINGS = "SECTION_SETTINGS"
    SECTION_PROFILE = "SECTION_PROFILE"
    SECTION_ADS = "SECTION_ADS"
    SECTION_ADD_ADS = "SECTION_ADD_ADS"

    ADS_PUBLISHED = "ADS_PUBLISHED"
    ADS_PUBLISHING = "ADS_PUBLISHING"
    NEW_OFFER = "NEW_OFFER"

    GENERIC_ERROR = "GENERIC_ERROR"


Currency = constr(min_length=2, max_length=5)
Balance = Dict[Currency, Decimal]
DBId = int
PaymentMethod = str
