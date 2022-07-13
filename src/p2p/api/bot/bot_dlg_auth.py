import operator
from inspect import iscoroutinefunction
from typing import Any

from aiogram.types import CallbackQuery, Message, ParseMode
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (Button, Cancel, Group, Select, Start,
                                        Url)
from aiogram_dialog.widgets.text import Const, Format, Jinja
from dependency_injector.wiring import Provide, inject
from loguru import logger
from p2p.application import AdsData, MerchMediatorRepo, UserInteractionEnum
from p2p.wiring import Container as wiring

from .bot_common import (Buttons, StAds, StAdsChoosing, StAdsTyping,
                         StOffersMain, get_userdata, save_userdata)
from .bot_i18n import (BUTTONS, CONSTRUCTION, INFO, KEYBOARD, OPTIONS, REMOVE,
                       WARNING, get_text)


@inject
async def get_my_offers(
    dialog_manager: DialogManager,
    merch_media_repo: MerchMediatorRepo = Provide[wiring.merch_media_repo],
    **kwargs,
):
    if hasattr(dialog_manager.event, "from_id"):
        user_id: str = dialog_manager.event.from_id
    elif hasattr(dialog_manager.event, "message"):
        user_id: str = dialog_manager.event.message["chat"].id
    else:
        raise ValueError("user_id not found")
    try:
        offers = await merch_media_repo.my_offers(user_id)
        return {"offers": offers}

    except:
        await dialog_manager.done()


offers_html = Jinja(
    """
<b>Offers</b>
{% for offer in offers %}
* {{ offer.asset }} {{ offer.fiat }} {{ offer.amount }}@{{ offer.price }} {{ offer.participants[0] }} - {{ offer.participants[1] }}
{% else %}
No offers...
{% endfor %}
"""
)

dlg_my_offers = Dialog(
    Window(
        Const(INFO),
        offers_html,
        Cancel(text=Const("Ok")),
        parse_mode=ParseMode.HTML,
        state=StOffersMain.default,
        getter=get_my_offers,
    ),
)


async def get_hint(
    dialog_manager: DialogManager,
    **kwargs,
):
    lang = "en"
    if hasattr(dialog_manager.event, "from_id"):
        user_id = dialog_manager.event.from_id
    elif hasattr(dialog_manager.event, "message"):
        user_id = dialog_manager.event.message["chat"].id
    user_data = await get_userdata(user_id)
    lang = user_data.settings.language
    return {
        "hint": get_text(UserInteractionEnum.SECTION_ADS, lang=lang),
        "btns": BUTTONS[lang],
    }


ads_html = Jinja(
    """
<b>Ads</b>
{% for ad in ads %}
* {{ ad.direction }} {{ ad.asset }} ({{ ad.min_amount }}-{{ ad.max_amount }} {{ ad.fiat }})@{{ ad.price }}
{% else %}
No ads...
{% endfor %}
"""
)


@inject
async def get_my_ads(
    dialog_manager: DialogManager,
    merch_media_repo: MerchMediatorRepo = Provide[wiring.merch_media_repo],
    **kwargs,
):
    if hasattr(dialog_manager.event, "from_id"):
        user_id: str = dialog_manager.event.from_id
    elif hasattr(dialog_manager.event, "message"):
        user_id: str = dialog_manager.event.message["chat"].id
    else:
        raise ValueError("user_id not found")
    try:
        ads = await merch_media_repo.my_ads(user_id)
        return {"ads": ads}
    except:
        await dialog_manager.done()


@inject
async def get_my_ads_del(
    dialog_manager: DialogManager,
    merch_media_repo: MerchMediatorRepo = Provide[wiring.merch_media_repo],
    **kwargs,
):
    if hasattr(dialog_manager.event, "from_id"):
        user_id: str = dialog_manager.event.from_id
    elif hasattr(dialog_manager.event, "message"):
        user_id: str = dialog_manager.event.message["chat"].id
    else:
        raise ValueError("user_id not found")
    try:
        ads = await merch_media_repo.my_ads(user_id)
        return {"ads": ads, **{f"{i}_active": True for i in range(len(ads))}}
    except:
        await dialog_manager.done()


@inject
async def on_del_clicked(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    merch_media_repo: MerchMediatorRepo = Provide[wiring.merch_media_repo],
    **kwargs,
):
    if button.widget_id is None:
        raise ValueError("Can't get button id")
    if hasattr(manager.event, "from_id"):
        user_id: str = manager.event.from_id
    elif hasattr(manager.event, "message"):
        user_id: str = manager.event.message["chat"].id
    else:
        raise ValueError("user_id not found")
    ad_id = int(button.widget_id.split("_")[1])
    try:
        ads = await merch_media_repo.my_ads(user_id)
        await merch_media_repo.delete_ads(
            user_id=user_id, ads_id=ads[ad_id]["offer_id"]
        )
    finally:
        await manager.done()


async def get_ads_details(dialog_manager: DialogManager, **kwargs):
    if hasattr(dialog_manager.event, "from_id"):
        user_id: str = dialog_manager.event.from_id
    elif hasattr(dialog_manager.event, "message"):
        user_id: str = dialog_manager.event.message["chat"].id
    else:
        raise ValueError("user_id not found")
    user_data = await get_userdata(user_id)
    lang = user_data.settings.language
    help_msg = get_text(UserInteractionEnum.SECTION_ADD_ADS, lang=lang)
    combined = [
        f"{hm}: [{v or WARNING}]"
        for hm, v in zip(help_msg.split("\n"), user_data.ads.dict().values())
    ]

    result = {
        "hint": "\n".join(combined),
        "btns": BUTTONS[lang],
    }
    if all({v is not None and v != "" for v in user_data.ads.dict().values()}):
        result["all_filled"] = "True"
    return result


async def ads_typing_handler(m: Message, dialog: Dialog, manager: DialogManager):
    feature = manager.current_context().start_data["source"].value.lower()
    lang = "en"
    try:
        user_data = await get_userdata(m["chat"].id)
        lang = user_data.settings.language
        old_ads = user_data.ads
        user_data.ads = AdsData(**old_ads.dict(exclude={feature}), **{feature: m.text})
        await save_userdata(user_data)
    except Exception as ex:
        logger.exception(ex)
        await m.answer(get_text(UserInteractionEnum.GENERIC_ERROR, lang=lang))
    finally:
        await manager.done()


dlg_ads_input = Dialog(
    Window(
        Const(KEYBOARD),
        Cancel(),
        MessageInput(ads_typing_handler),
        state=StAdsTyping.default,
    ),
)


async def on_ads_choices(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
):
    feature = manager.current_context().start_data["source"].value.lower()
    lang = "en"
    try:
        user_data = await get_userdata(c["from"].id)
        lang = user_data.settings.language
        old_ads = user_data.ads
        user_data.ads = AdsData(**old_ads.dict(exclude={feature}), **{feature: item_id})
        await save_userdata(user_data)
    except Exception as ex:
        logger.exception(ex)
        await c.message.answer(get_text(UserInteractionEnum.GENERIC_ERROR, lang=lang))
    finally:
        await manager.done()


@inject
async def get_choices(
    dialog_manager: DialogManager,
    merch_media_repo: MerchMediatorRepo = Provide[wiring.merch_media_repo],
    **kwargs,
):
    if hasattr(dialog_manager.event, "from_id"):
        user_id: str = dialog_manager.event.from_id
    elif hasattr(dialog_manager.event, "message"):
        user_id: str = dialog_manager.event.message["chat"].id
    else:
        raise ValueError("user_id not found")
    callback2prop_map = {
        Buttons.DIRECTION: merch_media_repo.direction,
        Buttons.ASSET: merch_media_repo.asset,
        Buttons.PAYMENT_METHOD: merch_media_repo.pay_method,
        Buttons.TIME_LIMIT: merch_media_repo.time_limit,
    }
    user_data = await get_userdata(user_id)
    lang = user_data.settings.language
    try:
        feature = dialog_manager.current_context().start_data["source"].value
        func = callback2prop_map[Buttons(feature)]
        if iscoroutinefunction(func):
            opts = await func(user_id)
        else:
            opts = func()
        return {
            "hint": get_text(UserInteractionEnum.ASK_CHOICE, lang=lang),
            "opts": [(o, o) for o in opts],
        }
    except:
        await dialog_manager.done()


dlg_ads_choice = Dialog(
    Window(
        Const(OPTIONS),
        Format("{hint}"),
        Group(
            Select(
                Format("{item[1]}"),
                id="s_opts",
                item_id_getter=operator.itemgetter(0),
                items="opts",
                on_click=on_ads_choices,
            ),
            width=2,
        ),
        Cancel(),
        state=StAdsChoosing.default,
        getter=get_choices,
    ),
)


@inject
async def on_post_ads(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    merch_media_repo: MerchMediatorRepo = Provide[wiring.merch_media_repo],
    **kwargs,
):
    lang = "en"
    try:
        user_id = c["from"].id
        user_data = await get_userdata(user_id)
        lang = user_data.settings.language
        if not user_data.profile.is_complete:
            raise ValueError("profile is not filled")

        # TODO: move to specific adapter
        ads_mapping = {
            "direction": "direction",
            "asset": "asset",
            "fiat": "fiat",
            "asset_amount": "initial_amount",
            "payment_method": "payment_methods",
            "time_limit": "time_limit",
            "min_amount": "min_amount",
            "max_amount": "max_amount",
        }
        settings_mapping = {
            "spread_comp": "min_comp_spread",
            "spread": "min_spread",
            "interception": "interception_threshold",
            "payment_comment": "payment_comment",
            "nick_name": "merchant_name",
        }
        ads = {
            ads_mapping[k]: v
            for k, v in user_data.ads.dict().items()
            if k in ads_mapping
        }
        joined = user_data.profile.dict()
        joined.update(user_data.settings.dict())
        settings_d = {
            settings_mapping[k]: v for k, v in joined.items() if k in settings_mapping
        }
        settings_d["user_id"] = user_id
        await merch_media_repo.post_ads(
            user_data.profile.login, ads=ads, settings=settings_d
        )
    except Exception as ex:
        logger.exception(ex)
        await c.message.answer(get_text(UserInteractionEnum.GENERIC_ERROR, lang=lang))
    finally:
        await manager.done()


dlg_ads_menu = Dialog(
    Window(
        Format("{hint}"),
        Group(
            *(
                Start(
                    Format(f"{{btns[{btn}]}}"),
                    id=btn,
                    state=st,
                )
                for btn, st in zip(
                    (
                        Buttons.NEW,
                        Buttons.LIST,
                        Buttons.DELETE,
                    ),
                    (StAds.input, StAds.list, StAds.delete),
                )
            ),
            Cancel(text=Const("Back")),
            width=2,
        ),
        getter=get_hint,
        state=StAds.default,
    ),
    Window(
        Const(INFO),
        ads_html,
        Cancel(Const("Ok")),
        parse_mode=ParseMode.HTML,
        state=StAds.list,
        getter=get_my_ads,
    ),
    Window(
        Const(REMOVE),
        ads_html,
        Group(
            *(
                Button(
                    Const(f"Ads #{i}"),
                    id=f"del_{i}",
                    on_click=on_del_clicked,
                    when=f"{i}_active",
                )
                for i in range(10)
            )
        ),
        Cancel(Const("Back")),
        state=StAds.delete,
        getter=get_my_ads_del,
        parse_mode=ParseMode.HTML,
    ),
    Window(
        Const(CONSTRUCTION),
        Format("{hint}"),
        Url(
            Const("Binance"),
            Const("https://www.binance.com/en/support/faq/360038038972"),
        ),
        Group(
            *(
                Start(
                    Format(f"{{btns[{btn}]}}"),
                    id=btn,
                    data={"source": btn},
                    state=StAdsTyping.default
                    if btn
                    in (
                        Buttons.FIAT,
                        Buttons.ASSET_AMOUNT,
                        Buttons.MIN_ORDER,
                        Buttons.MAX_ORDER,
                    )
                    else StAdsChoosing.default,
                )
                for btn in (
                    Buttons.DIRECTION,
                    Buttons.ASSET,
                    Buttons.FIAT,
                    Buttons.ASSET_AMOUNT,
                    Buttons.PAYMENT_METHOD,
                    Buttons.TIME_LIMIT,
                    Buttons.MIN_ORDER,
                    Buttons.MAX_ORDER,
                )
            ),
            width=2,
        ),
        Button(Const("Ok"), on_click=on_post_ads, id="place", when="all_filled"),
        Cancel(),
        state=StAds.input,
        getter=get_ads_details,
    ),
)
