import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram_dialog import DialogRegistry

from p2p.api.bot.aio_bot import dlg_notification, dlg_question, dlg_top_level
from p2p.api.bot.bot_common import StTopLevel
from p2p.api.bot.bot_dlg_auth import (dlg_ads_choice, dlg_ads_input,
                                      dlg_ads_menu, dlg_my_offers)
from p2p.api.bot.bot_dlg_profile import dlg_profile, dlg_profile_input
from p2p.api.bot.bot_dlg_settings import (dlg_settings, dlg_settings_choice,
                                          dlg_settings_input)
from p2p.wiring import Container

logging.basicConfig(level=logging.INFO)


async def main():
    # real main
    storage = MemoryStorage()
    bot = Bot(token=Container.bot_settings.tg_bot_key)
    dp = Dispatcher(bot, storage=storage)
    registry = DialogRegistry(dp)
    registry.register_start_handler(
        StTopLevel.default
    )  # resets stack and start dialogs on /start command
    registry.register(dlg_top_level)
    registry.register(dlg_question)
    registry.register(dlg_notification)

    registry.register(dlg_settings)
    registry.register(dlg_settings_input)
    registry.register(dlg_settings_choice)

    registry.register(dlg_profile)
    registry.register(dlg_profile_input)

    registry.register(dlg_my_offers)
    registry.register(dlg_ads_menu)
    registry.register(dlg_ads_input)
    registry.register(dlg_ads_choice)

    # render_transitions(registry)  # render graph with current transtions

    await dp.start_polling()


if __name__ == "__main__":
    container = Container()
    asyncio.run(main())
