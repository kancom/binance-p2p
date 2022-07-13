from typing import Dict, Optional

import emoji
from p2p.application import UserInteractionEnum

from .bot_common import Buttons

WARNING = emoji.emojize(":warning:")
KEYBOARD = emoji.emojize(":keyboard:")
INFO = emoji.emojize(":information:")
CONSTRUCTION = emoji.emojize(":construction:")
REMOVE = emoji.emojize(":cross_mark:")
OPTIONS = emoji.emojize(":balance_scale:")
HELP = emoji.emojize(":ring_buoy:")

MESSAGES: Dict[UserInteractionEnum, Dict[str, str]] = {
    UserInteractionEnum.AUTH_REQUIRED: {
        "en": f"{emoji.emojize(':warning:')} Auth required. Please wait for further question, then try again.\nIt may take several minutes!\nDon't try other auth actions;)",
        "ru": f"{emoji.emojize(':warning:')} Требуется аутентификация. Пожалуйста дождитесь дальнейших вопросов, а затем попробуйте снова.\nПроцесс занимает несколько минут!\nНе пытайтесь использовать другие действия требующие аутентификации;)",
    },
    UserInteractionEnum.AUTHENTICATED: {
        "en": f"{emoji.emojize(':next_track_button:')} Authenticated. Please go on",
        "ru": f"{emoji.emojize(':next_track_button:')} Аутентификация пройдена. Продолжайте",
    },
    UserInteractionEnum.ASK_AUTH_CODE: {
        "en": f"{emoji.emojize(':locked_with_pen:')} Send the code from your authenticator",
        "ru": f"{emoji.emojize(':locked_with_pen:')} Пришлите код с вашего аутентификационного устройства",
    },
    UserInteractionEnum.ASK_EMAIL_CODE: {
        "en": f"{emoji.emojize(':e-mail:')} Send the code from email",
        "ru": f"{emoji.emojize(':e-mail:')} Пришлите код из почты",
    },
    UserInteractionEnum.ASK_PHONE_CODE: {
        "en": f"{emoji.emojize(':mobile_phone:')} Send the code from sms",
        "ru": f"{emoji.emojize(':mobile_phone:')} Пришлите код из смс",
    },
    UserInteractionEnum.SECTION_START: {
        "en": (
            f"{emoji.emojize(':wrench:')} (Settings) Manage your settings\n"
            f"{emoji.emojize(':identification_card:')} (Profile) Set or update your profile\n"
            f"{emoji.emojize(':level_slider:')} (Advertisement) Manage your advertisements\n"
            f"{emoji.emojize(':incoming_envelope:')} (Offers)List your active offers (Auth){emoji.emojize(':shield:')}\n"
            f"{HELP} Show video explanation\n"
            "\n\n"
        ),
        "ru": (
            f"{emoji.emojize(':wrench:')} (Настройки) Общие настройки\n"
            f"{emoji.emojize(':identification_card:')} (Профиль) Настроить профиль\n"
            f"{emoji.emojize(':level_slider:')} (Обьявления) Настроить объявления\n"
            f"{emoji.emojize(':incoming_envelope:')} (Ордера) Показать активные заявки (Auth){emoji.emojize(':shield:')}\n"
            f"{HELP} Показать видео пояснение\n"
            "\n\n"
        ),
    },
    UserInteractionEnum.SECTION_SETTINGS: {
        "en": (
            f"{emoji.emojize(':globe_with_meridians:')} (Language/Язык): {emoji.emojize(':United_Kingdom:')} or {emoji.emojize(':Russia:')}\n"
            f"{emoji.emojize(':up-down_arrow:')} (Spread comp) Spread from opposite competitor\n"
            f"{emoji.emojize(':clamp:')} (Spread) from best opposite price\n\n"
            f"{emoji.emojize(':magnifying_glass_tilted_left:')} (Interception) percent by order volume\n to consider someone as a competitor\n\n"
            f"{emoji.emojize(':writing_hand:')} (Comment) for payment method in form\n"
            "MethodName - comment\n"
            "Papara - IBAN name: John Smith"
            "\n\n"
        ),
        "ru": (
            f"{emoji.emojize(':globe_with_meridians:')} (Language/Язык): {emoji.emojize(':United_Kingdom:')} или {emoji.emojize(':Russia:')}\n"
            f"{emoji.emojize(':up-down_arrow:')} (Спред конкурент) Спред со встречным конкурентом\n"
            f"{emoji.emojize(':clamp:')} (Спред) от лучшей встречной цены\n\n"
            f"{emoji.emojize(':magnifying_glass_tilted_left:')} (Пересечение) %% пересечения по объёмам\nчтобы считать как конкурента\n\n"
            f"{emoji.emojize(':writing_hand:')} (Комментарий) для платжного метода в форме:\n"
            "MethodName - comment\n"
            "Papara - IBAN name: John Smith"
            "\n\n"
        ),
    },
    UserInteractionEnum.SECTION_PROFILE: {
        "en": (
            f"{emoji.emojize(':key:')} (Login) @ binance\n"
            f"{emoji.emojize(':key:')} (Password) @ binance\n"
            f"{emoji.emojize(':bookmark:')} (Nick-name) Your p2p nick-name\n"
            "\n\n"
        ),
        "ru": (
            f"{emoji.emojize(':key:')} (Логин) Ваш логин на бинанс\n"
            f"{emoji.emojize(':key:')} (Пароль) Ваш пароль на бинанс\n"
            f"{emoji.emojize(':bookmark:')} (Никнейм) Ваше имя (ник) на бинанс p2p\n"
            "\n\n"
        ),
    },
    UserInteractionEnum.SECTION_ADD_ADS: {
        "en": (
            f"{emoji.emojize(':left-right_arrow:')} (Direction) Order direction (Buy/Sell) \n"
            f"{emoji.emojize(':bank:')} (Asset) Crypto Asset (USDT,...)\n"
            f"{emoji.emojize(':currency_exchange:')} (Fiat) currency (EUR,...)\n"
            f"{emoji.emojize(':credit_card:')} (Method) Payment Method @ binance (Auth){emoji.emojize(':shield:')}\n"
            f"{emoji.emojize(':input_numbers:')} (Amount) in asset crypto (click Binance below)\n"
            f"{emoji.emojize(':downwards_button:')} (Min) order amount in asset\n"
            f"{emoji.emojize(':upwards_button:')} (Max) order amount in asset\n"
            f"{emoji.emojize(':timer_clock:')} (Time) Max time to process order (by peer)\n\n"
            f"{emoji.emojize(':high_voltage:')} (Ok) - Send order to binance (Auth){emoji.emojize(':shield:')}"
            "\n\n"
        ),
        "ru": (
            f"{emoji.emojize(':left-right_arrow:')} (Направление) ордера (Buy/Sell) \n"
            f"{emoji.emojize(':bank:')} (Актив) Крипто актив (USDT,...)\n"
            f"{emoji.emojize(':currency_exchange:')} (Фиат) Фиатная валюта (EUR,...)\n"
            f"{emoji.emojize(':credit_card:')} (Способ оплаты) @ binance (Auth){emoji.emojize(':shield:')}\n"
            f"{emoji.emojize(':input_numbers:')} (Сумма) в крипто-активе (кнопка Binance ниже)\n"
            f"{emoji.emojize(':downwards_button:')} (Минимальный) объём сделки \n"
            f"{emoji.emojize(':upwards_button:')} (Максимальный) объём сделки \n"
            f"{emoji.emojize(':timer_clock:')} (Время) Максимальное время на обработку ордера\n\n"
            f"{emoji.emojize(':high_voltage:')} (Ok) - Отправить оредер на binance (Auth){emoji.emojize(':shield:')}"
            "\n\n"
        ),
    },
    UserInteractionEnum.ADS_PUBLISHED: {
        "en": f"{emoji.emojize(':vertical_traffic_light:')} Ads's been published",
        "ru": f"{emoji.emojize(':vertical_traffic_light:')} Опубликовано",
    },
    UserInteractionEnum.SECTION_ADS: {
        "en": (
            f"{emoji.emojize(':building_construction:')} (New) new ads\n"
            f"{emoji.emojize(':clipboard:')} (List) your ads (Auth){emoji.emojize(':shield:')}\n"
            f"{emoji.emojize(':litter_in_bin_sign:')} (Delete) an ads (Auth){emoji.emojize(':shield:')}\n"
            "(Back) Go to main menu"
            "\n\n"
        ),
        "ru": (
            f"{emoji.emojize(':building_construction:')} (Добавить) новое объявление\n"
            f"{emoji.emojize(':clipboard:')} (Показать) объявления (Auth){emoji.emojize(':shield:')}\n"
            f"{emoji.emojize(':litter_in_bin_sign:')} (Удалить) одно из объявлений (Auth){emoji.emojize(':shield:')}\n"
            "(Back) В главное меню"
            "\n\n"
        ),
    },
    UserInteractionEnum.ADS_PUBLISHING: {
        "en": "Your ads is being published",
        "ru": "Ваше объявление публикуется",
    },
    UserInteractionEnum.AUTH_FAILED: {
        "en": f"{emoji.emojize(':cloud_with_lightning_and_rain:')} Auth failed. Contact administrator",
        "ru": f"{emoji.emojize(':cloud_with_lightning_and_rain:')} Аутентификация НЕуспешна. Связаитесь с администратором",
    },
    UserInteractionEnum.NEW_OFFER: {
        "en": f"{emoji.emojize(':incoming_envelope:')} You've got an order",
        "ru": f"{emoji.emojize(':incoming_envelope:')} У вас новая заявка",
    },
    UserInteractionEnum.GENERIC_ERROR: {
        "en": f"{emoji.emojize(':bomb:')} An error occurred. Contact the admin",
        "ru": f"{emoji.emojize(':bomb:')} Ошибка. Обратитесь к админу",
    },
    UserInteractionEnum.ASK_CHOICE: {
        "en": "Select one of ...",
        "ru": "Выберите один из ...",
    },
}

BUTTONS: Dict[str, Dict[Buttons, str]] = {
    "en": {
        Buttons.SETTINGS: "Settings",
        Buttons.PROFILE: "Profile",
        Buttons.ADVERTISEMENTS: "Advertisements",
        Buttons.OFFERS: "Offers",
        Buttons.LOGIN: "Login",
        Buttons.PASSWORD: "Password",
        Buttons.NICK_NAME: "Nick name",
        Buttons.LANGUAGE: "Language",
        Buttons.SPREAD_COMP: "Spread Competitor",
        Buttons.SPREAD: "Spread",
        Buttons.INTERCEPTION: "Interception",
        Buttons.PAYMENT_COMMENT: "Comment",
        Buttons.DIRECTION: "Direction",
        Buttons.ASSET: "Asset",
        Buttons.FIAT: "Fiat",
        Buttons.ASSET_AMOUNT: "Amount",
        Buttons.PAYMENT_METHOD: "Method",
        Buttons.TIME_LIMIT: "Time",
        Buttons.MIN_ORDER: "Min",
        Buttons.MAX_ORDER: "Max",
        Buttons.NEW: "New",
        Buttons.LIST: "List",
        Buttons.DELETE: "Delete",
    },
    "ru": {
        Buttons.SETTINGS: "Настройки",
        Buttons.PROFILE: "Профиль",
        Buttons.ADVERTISEMENTS: "Обьявления",
        Buttons.OFFERS: "Ордера",
        Buttons.LOGIN: "Логин",
        Buttons.PASSWORD: "Пароль",
        Buttons.NICK_NAME: "Никнейм",
        Buttons.LANGUAGE: "Язык",
        Buttons.SPREAD_COMP: "Спред конкурент",
        Buttons.SPREAD: "Спред",
        Buttons.INTERCEPTION: "Пересечение",
        Buttons.PAYMENT_COMMENT: "Комментарий",
        Buttons.DIRECTION: "Направление",
        Buttons.ASSET: "Актив",
        Buttons.FIAT: "Фиат",
        Buttons.ASSET_AMOUNT: "Сумма",
        Buttons.PAYMENT_METHOD: "Способ оплаты",
        Buttons.TIME_LIMIT: "Время",
        Buttons.MIN_ORDER: "Мин",
        Buttons.MAX_ORDER: "Макс",
        Buttons.NEW: "Добавить",
        Buttons.LIST: "Показать",
        Buttons.DELETE: "Удалить",
    },
}


def get_text(
    interaction: UserInteractionEnum, arb: Optional[str] = None, lang: str = "en"
) -> str:
    msg = MESSAGES[interaction][lang]
    if arb is not None:
        msg = f"{msg} {arb}"
    return msg
