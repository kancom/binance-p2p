from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from p2p.api.celery_tasks import AdsInfo, publish_ads
from p2p.wiring import Container as wiring

from ..application.domain.common import Advertisement, PeerOffer
from ..application.repository.intention_repo import IntentionRepo
from ..application.repository.p2p_repo import P2POrderRepo

router = APIRouter()


@router.get("/pay-methods", response_model=List[str])
@inject
async def get_payment_methods(
    user_id: str, p2p_repo: P2POrderRepo = Depends(Provide[wiring.p2p_repo])
):
    return await p2p_repo.get_payment_methods(user_id)


@router.get("/my-ads", response_model=List[Advertisement])
@inject
async def get_my_ads(
    user_id: str, p2p_repo: P2POrderRepo = Depends(Provide[wiring.p2p_repo])
):
    return await p2p_repo.get_my_orders(user_id)


@router.delete("/my-ads", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_my_ads(
    user_id: str,
    ads_id: str,
    p2p_repo: P2POrderRepo = Depends(Provide[wiring.p2p_repo]),
):
    return await p2p_repo.delete_order(user_id, ads_id)


@router.post("/my-ads", status_code=status.HTTP_201_CREATED)
@inject
async def post_new_ads(
    ads_info: AdsInfo,
    intent_repo: IntentionRepo = Depends(Provide[wiring.intent_repo]),
):
    await intent_repo.save(ads_info.user_id, ads_info.ads, ads_info.settings)
    publish_ads.delay(ads_info.dict())


@router.get("/my-offers", response_model=List[PeerOffer])
@inject
async def get_my_offers(
    user_id: str, p2p_repo: P2POrderRepo = Depends(Provide[wiring.p2p_repo])
):
    return await p2p_repo.get_my_offer(user_id)
