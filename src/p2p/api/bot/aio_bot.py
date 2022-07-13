import asyncio
from datetime import datetime, timedelta

from aiogram.types import Message
from aiogram_dialog import BaseDialogManager, Dialog, DialogManager, Window
from aiogram_dialog.context.events import ShowMode
from aiogram_dialog.manager.protocols import LaunchMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel, Group, Start, Url
from aiogram_dialog.widgets.text import Const, Format
from dependency_injector.wiring import Provide, inject
from loguru import logger
from p2p.application import (MerchMediatorRepo, QueueRepo, UserInteractionEnum,
                             UserRepo, UserSettings)
from p2p.wiring import Container as wiring

from .bot_common import (Buttons, Feature, StAds, StNotification, StOffersMain,
                         StProfileMain, StQuestion, StSettingsMain, StTopLevel,
                         get_userdata, named_lock, save_userdata)
from .bot_i18n import BUTTONS, HELP, KEYBOARD, get_text


@inject
async def question_handler(
    m: Message,
    dialog: Dialog,
    manager: DialogManager,
    question_queue_repo=Provide[wiring.question_queue_repo],
):
    user_login = manager.current_context().start_data["user_login"]
    logger.debug(f"{user_login}, {m.text}")
    await question_queue_repo.put_answer(user_login, answer=m.text)
    user_data = await get_userdata(m.chat.id)
    del user_data.flex[Feature.question]
    await save_userdata(user_data)
    await manager.done()


async def get_question_hint(
    dialog_manager: DialogManager,
    **kwargs,
):
    return {"question": dialog_manager.current_context().start_data["text"]}


dlg_question = Dialog(
    Window(
        Const(KEYBOARD),
        Format("{question}"),
        MessageInput(question_handler),
        getter=get_question_hint,
        state=StQuestion.default,
    ),
)


dlg_notification = Dialog(
    Window(
        Format("{question}"),
        Cancel(text=Const("Ok")),
        getter=get_question_hint,
        state=StNotification.default,
    ),
    # launch_mode=LaunchMode.SINGLE_TOP,
)


@inject
async def question_job(
    user_id: str,
    user_login: str,
    manager: BaseDialogManager,
    question_queue_repo: QueueRepo = Provide[wiring.question_queue_repo],
) -> None:
    async with named_lock(user_id):
        while True:
            try:
                await asyncio.sleep(10)
                user_data = await get_userdata(user_id)
                now = datetime.utcnow()
                if Feature.question in user_data.flex and (
                    now - datetime.fromisoformat(user_data.flex[Feature.question])
                ) < timedelta(seconds=wiring.bot_settings.question_age):
                    continue
                question = await question_queue_repo.get_question(user_login)
                if question is not None:
                    logger.debug(question)
                    user_data.flex[Feature.question] = now.isoformat()
                    await manager.start(
                        StQuestion.default,
                        data={
                            "text": get_text(
                                lang=user_data.settings.language,
                                interaction=question,
                            ),
                            "user_login": user_login,
                        },
                        show_mode=ShowMode.SEND,
                    )
                    await save_userdata(user_data)
                else:
                    notification = await question_queue_repo.get_notification(
                        user_login
                    )
                    if notification is None:
                        notification = await question_queue_repo.get_notification(
                            user_id
                        )
                    if notification is not None:
                        text = get_text(
                            lang=user_data.settings.language,
                            interaction=notification.notification,
                        )
                        if notification.arbitrary:
                            text = f"{text} | {notification.arbitrary}"
                        # if notification.notification == UserInteractionEnum.NEW_OFFER:
                        #     await manager.bot.send_message(user_id, text=text)
                        # else:
                        await manager.start(
                            StNotification.default,
                            data={
                                "text": text,
                                "user_login": user_login,
                            },
                            show_mode=ShowMode.SEND,
                        )
            except Exception as ex:
                logger.error(ex)


@inject
async def get_hint(
    dialog_manager: DialogManager,
    user_repo: UserRepo = Provide[wiring.user_repo],
    **kwargs,
):
    lang = "en"
    try:
        if hasattr(dialog_manager.event, "from_id"):
            user_id: str = dialog_manager.event.from_id
        elif hasattr(dialog_manager.event, "message"):
            user_id: str = dialog_manager.event.message["chat"].id
        elif hasattr(dialog_manager.event, "from_user"):
            user_id: str = dialog_manager.event.from_user.id
        else:
            raise ValueError("user_id not found")
        try:
            user = await user_repo.get_by_presentation_id(user_id)
            try:
                asyncio.create_task(
                    question_job(
                        user_id=user_id,
                        user_login=user.login,
                        manager=dialog_manager.bg(),
                    )
                )
                logger.debug("periodic job has been set")
            except:
                pass
        except user_repo.NotFound as ex:
            logger.warning(ex)
        user_data = await get_userdata(user_id)
        lang = user_data.settings.language
        if lang == "":
            tg_lang = dialog_manager.event.from_user["language_code"]
            try:
                old_settings = user_data.settings
                feature = "language"
                user_data.settings = UserSettings(
                    **old_settings.dict(exclude={feature}), **{feature: tg_lang}
                )
            except:
                user_data.settings.language = "en"
            finally:
                await save_userdata(user_data)
                lang = user_data.settings.language
    except Exception as ex:
        logger.exception(ex)
        raise
    return {
        "hint": get_text(UserInteractionEnum.SECTION_START, lang=lang),
        "is_complete": user_data.profile.is_complete,
        "btns": BUTTONS[lang],
    }


dlg_top_level = Dialog(
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
                        Buttons.SETTINGS,
                        Buttons.PROFILE,
                    ),
                    (
                        StSettingsMain.default,
                        StProfileMain.default,
                    ),
                )
            ),
            *(
                Start(
                    Format(f"{{btns[{btn}]}}"),
                    id=btn,
                    state=st,
                    when=lambda d, w, m: d["is_complete"],
                )
                for btn, st in zip(
                    (
                        Buttons.ADVERTISEMENTS,
                        Buttons.OFFERS,
                    ),
                    (
                        StAds.default,
                        StOffersMain.default,
                    ),
                )
            ),
            Url(Const(HELP), Const("https://youtu.be/yYoqPptmIk4")),
            width=2,
        ),
        state=StTopLevel.default,
        getter=get_hint,
    ),
)
