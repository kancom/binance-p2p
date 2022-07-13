from datetime import datetime

from aiogram.types import Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel, Group, Start
from aiogram_dialog.widgets.text import Const, Format
from dependency_injector.wiring import Provide, inject
from loguru import logger
from p2p.application import User, UserInteractionEnum, UserProfile, UserRepo
from p2p.wiring import Container as wiring

from .bot_common import (Buttons, StProfile, StProfileMain, dict2str,
                         get_userdata, save_userdata)
from .bot_i18n import BUTTONS, KEYBOARD, WARNING, get_text


@inject
async def profile_handler(
    m: Message,
    dialog: Dialog,
    manager: DialogManager,
    user_repo: UserRepo = Provide[wiring.user_repo],
):
    feature = manager.current_context().start_data["source"].value.lower()
    user = None
    user_id = m["chat"].id

    user_data = await get_userdata(user_id)
    old_profile = user_data.profile
    try:
        user = await user_repo.get_by_presentation_id(user_id)
    except user_repo.NotFound as ex:
        logger.warning(ex)
        if old_profile.is_complete:
            user = User(
                **{k: v for k, v in user_data.profile.dict().items()},
                active_until=datetime.utcnow(),
                presentation_id=user_id,
            )
    finally:
        # sync user data with user from db
        if user is not None:
            for k in old_profile.dict().keys():
                setattr(old_profile, k, getattr(user, k))
        # update user data
        user_data.profile = UserProfile(
            **old_profile.dict(exclude={feature}), **{feature: m.text}
        )
        await save_userdata(user_data)
        # update user in db
        if old_profile.is_complete:
            user = User(
                **old_profile.dict(exclude={feature}),
                **{feature: m.text},
                active_until=datetime.utcnow(),
                presentation_id=user_id,
            )
            await user_repo.save(user)

        await manager.done()


@inject
async def get_profile_hint(
    dialog_manager: DialogManager,
    user_repo: UserRepo = Provide[wiring.user_repo],
    **kwargs,
):
    lang = "en"
    user = None
    if hasattr(dialog_manager.event, "from_id"):
        user_id = dialog_manager.event.from_id
    elif hasattr(dialog_manager.event, "message"):
        user_id = dialog_manager.event.message["chat"].id
    try:
        user = await user_repo.get_by_presentation_id(user_id)
    except user_repo.NotFound as ex:
        logger.warning(ex)
    finally:
        user_data = await get_userdata(user_id)
        lang = user_data.settings.language
        if user is not None:
            user_data.profile.password = user.password
            user_data.profile.login = user.login
            user_data.profile.nick_name = user.nick_name

        if user_data.profile.password:
            user_data.profile.password = "*" * len(user_data.profile.password)
        return {
            "hint": get_text(UserInteractionEnum.SECTION_PROFILE, lang=lang),
            "profile": dict2str(
                {k: v or WARNING for k, v in user_data.profile.dict().items()}
            ),
            "btns": BUTTONS[lang],
        }


dlg_profile_input = Dialog(
    Window(
        Const(KEYBOARD),
        Cancel(),
        MessageInput(profile_handler),
        state=StProfile.input,
    ),
)

dlg_profile = Dialog(
    Window(
        Format("{hint}"),
        Format("{profile}"),
        Group(
            *(
                Start(
                    Format(f"{{btns[{btn}]}}"),
                    id=btn,
                    data={"source": btn},
                    state=StProfile.input,
                )
                for btn in (Buttons.LOGIN, Buttons.PASSWORD, Buttons.NICK_NAME)
            ),
            width=2,
        ),
        Cancel(text=Const("Done")),
        getter=get_profile_hint,
        state=StProfileMain.default,
    ),
)
