from loguru import logger
from p2p.application.utils import calculate_price, get_comment
from p2p.settings import AdsSettings

from ..domain.common import Advertisement, Pair
from ..foundation import AdsFlow, Direction
from ..repository.intention_repo import IntentionRepo
from ..repository.p2p_repo import P2POrderRepo
from ..use_case.collect_info import CollectInfoUseCase


class PlaceOrderUseCase:
    def __init__(
        self,
        intent_repo: IntentionRepo,
        collect_info_uc: CollectInfoUseCase,
        p2p_repo: P2POrderRepo,
    ) -> None:
        self._intent_repo = intent_repo
        self._collect_info_uc = collect_info_uc
        self._p2p_repo = p2p_repo

    async def execute(self, user_id: str):
        try:
            ads = await self._intent_repo.read_with_status(
                uuid=user_id, status=AdsFlow.NEW
            )

            intent_id, ads_d, settings_d = ads[-1]
        except Exception as ex:
            logger.error(ex)
            raise
        try:
            logger.debug(f"Start placing {intent_id} for {user_id} user")

            pair = Pair(asset=ads_d["asset"], fiat=ads_d["fiat"])
            settings = AdsSettings(**settings_d)
            direction = Direction(ads_d["direction"].upper())
            pay_method = ads_d["payment_methods"]
            comment = get_comment(settings.payment_comment, pay_method)
            ads = Advertisement(
                payment_methods=[pay_method],
                direction=direction,
                asset=pair.asset,
                fiat=pair.fiat,
                price=0,  # stub, set later
                digits=2,  # stub, set later
                time_limit=int(ads_d["time_limit"]),
                buyer_reg_age=1,
                initial_amount=int(ads_d["initial_amount"]),
                min_amount=int(ads_d["min_amount"]),
                max_amount=int(ads_d["max_amount"]),
                remarks=comment,
                auto_reply=comment,
            )
            info_resp = await self._collect_info_uc.execute(
                ad=ads,
                method=ads_d["payment_methods"],
                settings=settings,
            )
            order_price = calculate_price(
                direction=direction,
                comp_spread=settings.min_comp_spread,
                spread=settings.min_spread,
                digits=info_resp.sell_competitor.digits,
                info_resp=info_resp,
            )
            competitor = (
                info_resp.sell_competitor
                if direction == Direction.SELL
                else info_resp.buy_competitor
            )
            ads.digits = competitor.digits
            ads.price = order_price
            logger.info(f"placing new order {ads}")
            await self._p2p_repo.place_order(settings_d["user_id"], ads)
            await self._intent_repo.set_status(intent_id, AdsFlow.PLACED)
        except Exception as ex:
            await self._intent_repo.set_status(intent_id, AdsFlow.FAILED)
            logger.error(ex)
            raise
