from typing import cast

from dependency_injector import containers, providers
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from p2p.infrastructure import (AlchemyAuthRepo, AlchemyIntentionRepo,
                                AlchemyUserRepo, BinanceAuthenticator,
                                BinanceMerchMediatorRepo, BinanceP2PRepo,
                                BinP2PAdapter, RedisOrderBookCacheRepo,
                                RedisQueueRepo, RedisUserDataRepo)
from p2p.settings import AdsSettings, BotSettings, CelerySettings, Settings


def get_async_db_engine(dsn: str) -> AsyncEngine:
    engine = cast(
        AsyncEngine,
        create_async_engine(dsn, echo=False, pool_pre_ping=True),
    )
    return engine


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["p2p.api"])
    # settings = Settings(_env_file=".env")
    # ads_settings = AdsSettings(_env_file=".env")
    settings = Settings()
    ads_settings = AdsSettings()
    bot_settings = BotSettings()
    celery_settings = CelerySettings()

    logger.debug(ads_settings)
    logger.debug(bot_settings)
    logger.debug(celery_settings)

    merch_media_repo = providers.Singleton(
        BinanceMerchMediatorRepo, settings.merch_api_url
    )
    db_engine = providers.Singleton(get_async_db_engine, settings.db_dsn)
    auth_repo = providers.Singleton(AlchemyAuthRepo, db_engine)
    user_repo = providers.Singleton(AlchemyUserRepo, db_engine)
    intent_repo = providers.Singleton(AlchemyIntentionRepo, db_engine)
    orderbook_cache_repo = providers.Singleton(
        RedisOrderBookCacheRepo, settings.redis_dsn
    )
    question_queue_repo = providers.Singleton(
        RedisQueueRepo,
        locker_repo=orderbook_cache_repo,
        redis_dsn=bot_settings.redis_dsn,
    )
    userdata_repo = providers.Singleton(
        RedisUserDataRepo,
        locker_repo=orderbook_cache_repo,
        redis_dsn=bot_settings.redis_dsn,
    )

    adapter = BinP2PAdapter()
    auth = providers.Singleton(
        BinanceAuthenticator,
        driver_url=ads_settings.driver_url,
        captcha_solver_key=ads_settings.captcha_solver_key,
        user_queue_repo=question_queue_repo,
    )
    p2p_repo = providers.Singleton(
        BinanceP2PRepo,
        adapter,
        auth_provider=auth,
        auth_repo=auth_repo,
        user_repo=user_repo,
        locker_repo=orderbook_cache_repo,
        user_question_repo=question_queue_repo,
    )
    # market_repo = BinanceMarketDataRepo(adapter=adapter)


# private_repo = BinancePrivateDataRepo(
#     adapter=adapter,
#     api_key=settings.binance_api_key,
#     secret_key=settings.binance_secret_key,
# )
# balances_uc = GetBalanceUseCase(
#     settings=settings,
#     market_repo=market_repo,
#     private_data_repo=private_repo,
# )
# manager = ManagerUseCase(
#     settings=settings,
#     p2prepo=p2p_repo,
#     balance_uc=balances_uc,
# )
