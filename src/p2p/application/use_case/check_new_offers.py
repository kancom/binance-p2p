import itertools as it

from loguru import logger

from ..foundation import AdsFlow, Exchange, UserInteractionEnum
from ..repository.inc_repo import IncrementRepo
from ..repository.intention_repo import IntentionRepo
from ..repository.p2p_repo import P2POrderRepo
from ..repository.queue_repo import QueueRepo


class CheckNewOffersUseCase:
    def __init__(
        self,
        p2p_repo: P2POrderRepo,
        notification_repo: QueueRepo,
        intent_repo: IntentionRepo,
        inc_repo: IncrementRepo,
    ) -> None:
        self._intent_repo = intent_repo
        self._p2p_repo = p2p_repo
        self._notification_repo = notification_repo
        self._inc_repo = inc_repo

    async def execute(self):
        try:
            ads = await self._intent_repo.read_with_status(status=AdsFlow.PLACED)
        except Exception as ex:
            logger.error(ex)
            raise
        for user_id, _ in it.groupby(ads, key=lambda a: a[2]["user_id"]):
            exchange = Exchange.BINANCE
            offers = await self._p2p_repo.get_my_offer(user_id)
            val = "".join([str(o.order_nb) for o in offers])
            is_new = await self._inc_repo.update(exchange, name=user_id, value=val)
            if not is_new:
                return
            for offer in offers:
                arb = f"Order: {offer.asset} {offer.fiat} {offer.amount:.2f}@{offer.price:.2f}"
                await self._notification_repo.put_notification(
                    user_id,
                    notification=UserInteractionEnum.NEW_OFFER,
                    arbitrary=arb,
                )
