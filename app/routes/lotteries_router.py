from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from app.database.models import Lottery
from app.database.models.lottery_prizes import LotteryPrizes
from app.schemas.lottery_schema import (
    IFullLotteryInfo,
    IGetLotteriesResponse,
    ILotteryInfo,
)
from app.services.lottery_service import get_available_nft_count

router = APIRouter(tags=["lotteries"])


@router.get(
    "/lotteries",
    response_model=IGetLotteriesResponse
)
async def get_lotteries(user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)

    # Получаем все лотереи с датой >= сейчас
    lotteries = await Lottery.filter(event_date__gte=now).order_by("event_date")

    active = next((l for l in lotteries if l.is_active), None)
    if not active:
        raise HTTPException(status_code=404, detail="Active lottery not found")

    future = [l for l in lotteries if not l.is_active]

    # Количество доступных и общее количество NFT
    available_nft = await get_available_nft_count(active.id)
    total_nft = await LotteryPrizes.filter(lottery=active).count()

    # Активная лотерея
    active_data = IFullLotteryInfo(
        id=active.id,
        name=active.name,
        short_description=active.short_description,
        banner=active.banner,
        collection_banner=active.collection_banner,
        event_date=int(active.event_date.timestamp()),
        totalSum=active.total_sum,
        availableNftCount=available_nft,
        totalNftCount=total_nft,
        grandPrizes=[],
        prizes=[],
        winners=[],
    )

    # Будущие лотереи
    future_data = [
        ILotteryInfo(
            id=l.id,
            name=l.name,
            short_description=l.short_description,
            banner=l.banner,
            collection_banner=l.collection_banner,
            event_date=int(l.event_date.timestamp()),
        )
        for l in future
    ]

    return IGetLotteriesResponse(
        activeLottery=active_data,
        futureLotteries=future_data,
    )
