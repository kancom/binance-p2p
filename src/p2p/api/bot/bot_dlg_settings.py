import operator
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel, Group, Select, Start
from aiogram_dialog.widgets.text import Const, Format
from dependency_injector.wiring import Provide, inject
from loguru import logger
from p2p.application import (MerchMediatorRepo, UserInteractionEnum,
                             UserSettings)
from p2p.wiring import Container as wiring

from .bot_common import (Buttons, StSettings, StSettingsLang, StSettingsMain,
                         dict2str, get_userdata, save_userdata)
from .bot_i18n import BUTTONS, KEYBOARD, OPTIONS, WARNING, get_text


async def get_settings_hint(dialog_manager: DialogManager, **kwargs):
    lang = "en"
    try:
        if hasattr(dialog_manager.event, "from_id"):
            user_id = dialog_manager.event.from_id
        elif hasattr(dialog_manager.event, "message"):
            user_id = dialog_manager.event.message["chat"].id
        user_data = await get_userdata(user_id)
        lang = user_data.settings.language
    except Exception as ex:
        logger.exception(ex)
        raise
    return {
        "hint": get_text(UserInteractionEnum.SECTION_SETTINGS, lang=lang),
        "settings": dict2str(
            {k: v or WARNING for k, v in user_data.settings.dict().items()}
        ),
        "btns": BUTTONS[lang],
    }


async def settings_handler(m: Message, dialog: Dialog, manager: DialogManager):
    feature = manager.current_context().start_data["source"].value.lower()
    lang = "en"
    try:
        user_data = await get_userdata(m["chat"].id)
        lang = user_data.settings.language
        old_settings = user_data.settings
        user_data.settings = UserSettings(
            **old_settings.dict(exclude={feature}), **{feature: m.text}
        )
        await save_userdata(user_data)
    except Exception as ex:
        logger.exception(ex)
        await m.answer(get_text(UserInteractionEnum.GENERIC_ERROR, lang=lang))
    finally:
        await manager.done()


dlg_settings_input = Dialog(
    Window(
        Const(KEYBOARD),
        Cancel(),
        MessageInput(settings_handler),
        state=StSettings.input,
    ),
)


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
        Buttons.LANGUAGE: lambda: ("en", "ru"),
    }
    user_data = await get_userdata(user_id)
    lang = user_data.settings.language
    try:
        feature = dialog_manager.current_context().start_data["source"].value
        func = callback2prop_map[Buttons(feature)]
        opts = func()
        return {
            "hint": get_text(UserInteractionEnum.ASK_CHOICE, lang=lang),
            "opts": [(o, o) for o in opts],
        }
    except:
        await dialog_manager.done()


async def on_settings_choices(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
):
    feature = manager.current_context().start_data["source"].value.lower()
    lang = "en"
    try:
        user_data = await get_userdata(c["from"].id)
        lang = user_data.settings.language
        old_settings = user_data.settings
        user_data.settings = UserSettings(
            **old_settings.dict(exclude={feature}), **{feature: item_id}
        )
        await save_userdata(user_data)
    except Exception as ex:
        logger.exception(ex)
        await c.message.answer(get_text(UserInteractionEnum.GENERIC_ERROR, lang=lang))
    finally:
        await manager.done()


dlg_settings_choice = Dialog(
    Window(
        Const(OPTIONS),
        Format("{hint}"),
        Group(
            Select(
                Format("{item[1]}"),
                id="s_opts",
                item_id_getter=operator.itemgetter(0),
                items="opts",
                on_click=on_settings_choices,
            ),
            width=2,
        ),
        Cancel(),
        state=StSettingsLang.default,
        getter=get_choices,
    ),
)
dlg_settings = Dialog(
    Window(
        Format("{hint}"),
        Format("{settings}"),
        Group(
            *(
                Start(
                    Format(f"{{btns[{btn}]}}"),
                    id=btn,
                    data={"source": btn},
                    state=StSettings.input
                    if btn != Buttons.LANGUAGE
                    else StSettingsLang.default,
                )
                for btn in (
                    Buttons.LANGUAGE,
                    Buttons.SPREAD_COMP,
                    Buttons.SPREAD,
                    Buttons.INTERCEPTION,
                    Buttons.PAYMENT_COMMENT,
                )
            ),
            width=2,
        ),
        Cancel(text=Const("Done")),
        getter=get_settings_hint,
        state=StSettingsMain.default,
    ),
    # on_process_result=process_result,
)
