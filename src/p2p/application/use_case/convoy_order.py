import itertools as it
from datetime import datetime, timedelta

from loguru import logger
from p2p.settings import AdsSettings

from ..domain.common import ConvoyAdaptiveInterval, INTERVAL_TRACKER
from ..foundation import AdsFlow, Direction
from ..repository.intention_repo import IntentionRepo
from ..repository.p2p_repo import P2POrderRepo
from ..use_case.collect_info import CollectInfoUseCase
from ..utils import calculate_price

MAX_POLL_INTERVAL = 60
POLL_TRACK_LEN = 10


class ConvoyOrderUseCase:
    def __init__(
        self,
        intent_repo: IntentionRepo,
        collect_info_uc: CollectInfoUseCase,
        p2p_repo: P2POrderRepo,
    ) -> None:
        self._intent_repo = intent_repo
        self._collect_info_uc = collect_info_uc
        self._p2p_repo = p2p_repo

    async def execute(self):
        try:
            ads = await self._intent_repo.read_with_status(status=AdsFlow.PLACED)
        except Exception as ex:
            logger.error(ex)
            raise
        try:
            now = datetime.utcnow()
            for user_id, user_ads in it.groupby(ads, key=lambda a: a[2]["user_id"]):
                if user_id not in INTERVAL_TRACKER:
                    INTERVAL_TRACKER[user_id] = ConvoyAdaptiveInterval(history=[now])
                if (
                    INTERVAL_TRACKER[user_id].history[-1]
                    + INTERVAL_TRACKER[user_id].current
                    >= now
                ):
                    continue
                existing_orders = await self._p2p_repo.get_my_orders(user_id=user_id)
                for intent_id, user_ad, settings_d in user_ads:
                    direction = Direction(user_ad["direction"].upper())
                    similars = [
                        eo
                        for eo in existing_orders
                        if (
                            eo.asset.upper() == user_ad["asset"].upper()
                            and eo.fiat.upper() == user_ad["fiat"].upper()
                            and eo.direction == direction
                            and eo.payment_methods[0].upper()
                            == user_ad["payment_methods"].upper()
                            and eo.initial_amount == int(user_ad["initial_amount"])
                        )
                    ]
                    if len(similars) == 0:
                        await self._intent_repo.set_status(intent_id, AdsFlow.COMPLETED)
                        continue
                    elif len(similars) > 1:
                        logger.warning(f"more than 1 similar ads found. Skip")
                        continue

                    existing_ad = similars[0]
                    settings = AdsSettings(**settings_d)
                    info_resp = await self._collect_info_uc.execute(
                        ad=existing_ad,
                        method=user_ad["payment_methods"],
                        settings=settings,
                    )
                    order_price = calculate_price(
                        direction=direction,
                        comp_spread=settings.min_comp_spread,
                        spread=settings.min_spread,
                        digits=info_resp.sell_competitor.digits,
                        info_resp=info_resp,
                    )
                    if order_price != existing_ad.price:
                        INTERVAL_TRACKER[user_id] = ConvoyAdaptiveInterval(
                            history=[now]
                        )
                        logger.debug(
                            f"adjusting ad for {user_id} from {existing_ad.price} to {order_price}"
                        )
                        existing_ad.price = order_price
                        await self._p2p_repo.update_order(user_id, existing_ad)
                    else:
                        INTERVAL_TRACKER[user_id].history.append(now)
                        if len(INTERVAL_TRACKER[user_id].history) >= POLL_TRACK_LEN:
                            INTERVAL_TRACKER[user_id] = ConvoyAdaptiveInterval(
                                history=[now],
                                current=min(
                                    2 * INTERVAL_TRACKER[user_id].current,
                                    timedelta(seconds=MAX_POLL_INTERVAL),
                                ),
                            )

        except Exception as ex:
            logger.error(ex)
            raise
