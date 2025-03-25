from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Path

from app.auth.dependencies import get_current_user
from app.database.models import Lottery
from app.database.models.lottery_prizes import LotteryPrizes
from app.schemas.lottery_schema import (
    IFullLotteryInfo,
    IGetLotteriesResponse,
    ILotteryHistoryInfo,
    ILotteryInfo,
    IGetLotteriesHistoryResponse
)
from app.services.lottery_service import get_available_nft_count

router = APIRouter(tags=["lotteries"])


@router.get(
    "/lotteries",
    response_model=IGetLotteriesResponse
)
async def get_lotteries(user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)

    lotteries = await Lottery.filter(event_date__gte=now).order_by("event_date")

    active = next((l for l in lotteries if l.is_active), None)
    if not active:
        raise HTTPException(status_code=404, detail="Active lottery not found")

    future = [l for l in lotteries if not l.is_active]

    available_nft = await get_available_nft_count(active.id)
    total_nft = await LotteryPrizes.filter(lottery=active).count()

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


@router.get("/lotteries/history", response_model=IGetLotteriesHistoryResponse)
async def get_lottery_history(
    page: int = Query(..., ge=1),
    limit: int = Query(10, ge=1),
    q: str | None = None,
    user=Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    offset = (page - 1) * limit
    query = Lottery.filter(event_date__lt=now, is_active=False)
    
    if q:
        query = query.filter(name__icontains=q)
        
    lotteries = await query.offset(offset).limit(limit)
    result: list[ILotteryHistoryInfo] = []
    
    for l in lotteries:
        total_nft_count = await LotteryPrizes.filter(lottery=l).count()
        result.append(ILotteryHistoryInfo(
            id=l.id,
            name=l.name,
            event_date=int(l.event_date.timestamp()),
            totalNftCount=total_nft_count,
            ticket_price=l.ticket_price,
        ))
        
    return IGetLotteriesHistoryResponse(lotteries=result)


@router.get("/lotteries/{lottery_id}", response_model=IGetLotteriesResponse)
async def get_lottery_by_id(
    lottery_id: int = Path(..., ge=1),
    user=Depends(get_current_user)
):
    lottery = await Lottery.get_or_none(id=lottery_id)
    if not lottery:
        raise HTTPException(status_code=404, detail="Lottery not found")
    
    available_nft = await get_available_nft_count(lottery.id)
    total_nft = await LotteryPrizes.filter(lottery=lottery).count()
    
    active_data = IFullLotteryInfo(
        id=lottery.id,
        name=lottery.name,
        short_description=lottery.short_description,
        banner=lottery.banner,
        collection_banner=lottery.collection_banner,
        event_date=int(lottery.event_date.timestamp()),
        totalSum=lottery.total_sum,
        availableNftCount=available_nft,
        totalNftCount=total_nft,
        grandPrizes=[],
        prizes=[],
        winners=[],
        otherLotteries=[],
    )
    
    other_lotteries = await Lottery.exclude(id=lottery.id).order_by("-event_date").limit(5)
    
    future_data = [
        ILotteryInfo(
            id=l.id,
            name=l.name,
            short_description=l.short_description,
            banner=l.banner,
            collection_banner=l.collection_banner,
            event_date=int(l.event_date.timestamp()),
        )
        for l in other_lotteries
    ]
    
    active_data.otherLotteries = future_data
    
    return IGetLotteriesResponse(
        activeLottery=active_data,
        futureLotteries=[]
    )