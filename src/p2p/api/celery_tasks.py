import asyncio
from typing import Dict

from dependency_injector.wiring import Provide, inject
from loguru import logger
from p2p.application import IncrementRepo
from p2p.application.foundation import Exchange
from p2p.wiring import Container as wiring
from pydantic.main import BaseModel

from ..application.foundation import UserInteractionEnum
from ..application.repository.intention_repo import IntentionRepo
from ..application.repository.orderbook_cache_repo import OrderBookCacheRepo
from ..application.repository.p2p_repo import P2POrderRepo
from ..application.repository.queue_repo import QueueRepo
from ..application.use_case.check_new_offers import CheckNewOffersUseCase
from ..application.use_case.collect_info import CollectInfoUseCase
from ..application.use_case.convoy_order import ConvoyOrderUseCase
from ..application.use_case.place_order import PlaceOrderUseCase
from .celery_main import app as celery_app


class AdsInfo(BaseModel):
    user_id: str
    ads: Dict
    settings: Dict


def get_loop():
    asyncio.get_event_loop()


@inject
async def place_order(
    ads_info: AdsInfo,
    intent_repo: IntentionRepo = Provide[wiring.intent_repo],
    p2p_repo: P2POrderRepo = Provide[wiring.p2p_repo],
    ob_cache: OrderBookCacheRepo = Provide[wiring.orderbook_cache_repo],
    question_repo: QueueRepo = Provide[wiring.question_queue_repo],
):
    collect_info_uc = CollectInfoUseCase(
        p2p_repo=p2p_repo, ob_cache=ob_cache, exchange=Exchange.BINANCE
    )
    place_order_uc = PlaceOrderUseCase(
        intent_repo=intent_repo, collect_info_uc=collect_info_uc, p2p_repo=p2p_repo
    )
    try:
        await place_order_uc.execute(ads_info.user_id)
    except Exception as ex:
        logger.error(ex)
        await question_repo.put_notification(
            ads_info.user_id, UserInteractionEnum.GENERIC_ERROR
        )
        raise
    await question_repo.put_notification(
        ads_info.user_id, notification=UserInteractionEnum.ADS_PUBLISHED
    )


@inject
async def convoy_orders(
    intent_repo: IntentionRepo = Provide[wiring.intent_repo],
    p2p_repo: P2POrderRepo = Provide[wiring.p2p_repo],
    ob_cache: OrderBookCacheRepo = Provide[wiring.orderbook_cache_repo],
):
    collect_info_uc = CollectInfoUseCase(
        p2p_repo=p2p_repo, ob_cache=ob_cache, exchange=Exchange.BINANCE
    )
    convoy_orders_uc = ConvoyOrderUseCase(
        intent_repo=intent_repo, collect_info_uc=collect_info_uc, p2p_repo=p2p_repo
    )
    try:
        await convoy_orders_uc.execute()
    except Exception as ex:
        logger.error(ex)
        raise


@inject
async def check_new_orders(
    p2p_repo: P2POrderRepo = Provide[wiring.p2p_repo],
    notification_repo: QueueRepo = Provide[wiring.question_queue_repo],
    increment_repo: IncrementRepo = Provide[wiring.orderbook_cache_repo],
    intent_repo: IntentionRepo = Provide[wiring.intent_repo],
):
    uc = CheckNewOffersUseCase(
        p2p_repo=p2p_repo,
        notification_repo=notification_repo,
        inc_repo=increment_repo,
        intent_repo=intent_repo,
    )
    try:
        await uc.execute()
    except Exception as ex:
        logger.error(ex)
        raise


@celery_app.task()
def publish_ads(
    ads_info: dict,
):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(place_order(ads_info=AdsInfo(**ads_info)))


@celery_app.task()
def convoy_ads():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(convoy_orders())


@celery_app.task()
def new_order():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_new_orders())
