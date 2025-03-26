from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Path, WebSocket, WebSocketDisconnect
from tortoise.expressions import Q

from app.auth.dependencies import get_current_user
from app.database.models import Lottery
from app.database.models.lottery_prizes import LotteryPrizes
from app.database.models.ticket import Ticket
from app.database.models.user_prizes import UserPrizes
from app.schemas.lottery_schema import (
    ICheckLiveResponse,
    IFullLotteryInfo,
    IGetLotteriesResponse,
    IGetNftTokensResponse,
    ILotteryHistoryInfo,
    ILotteryInfo,
    IGetLotteriesHistoryResponse,
    IMarketNftToken,
    LiveStatus,
    WinnerItem,
    WinnerUpdate
)
from app.services.lottery_service import get_available_nft_count

router = APIRouter(tags=["lotteries"], prefix="/lotteries")


@router.get("", response_model=IGetLotteriesResponse)
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
        total_sum=active.total_sum,
        available_nft_count=available_nft,
        total_nft_count=total_nft,
        grand_prizes=[],
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
        active_lottery=active_data,
        future_lotteries=future_data,
    )


@router.get("/status", response_model=ICheckLiveResponse)
async def get_live_status(user=Depends(get_current_user)):
    # TODO Check status logic
    return ICheckLiveResponse(
        status=LiveStatus.OFFLINE,
        live_link=None
    )


@router.get("/history", response_model=IGetLotteriesHistoryResponse)
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
            total_nft_count=total_nft_count,
            ticket_price=l.ticket_price,
        ))

    return IGetLotteriesHistoryResponse(lotteries=result)


@router.get("/{lottery_id}", response_model=IGetLotteriesResponse)
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
        total_sum=lottery.total_sum,
        available_nft_count=available_nft,
        total_nft_count=total_nft,
        grand_prizes=[],
        prizes=[],
        winners=[],
        other_lotteries=[],
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

    active_data.other_lotteries = future_data

    return IGetLotteriesResponse(
        active_lottery=active_data,
        future_lotteries=[]
    )


@router.get("/nfts/{lottery_id}", response_model=IGetNftTokensResponse)
async def get_lottery_nfts(
    lottery_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    min_number: int | None = Query(None),
    max_number: int | None = Query(None),
    user=Depends(get_current_user)
):
    offset = (page - 1) * limit
    lottery = await Lottery.get_or_none(id=lottery_id)

    if not lottery:
        raise HTTPException(status_code=404, detail="Lottery not found")

    filters = Q(lottery_id=lottery_id)
    if min_number is not None:
        filters &= Q(number__gte=min_number)
    if max_number is not None:
        filters &= Q(number__lte=max_number)

    total = await Ticket.filter(filters).count()
    total_pages = (total + limit - 1) // limit
    tickets = await Ticket.filter(filters).offset(offset).limit(limit).all()

    nfts = [
        IMarketNftToken(
            id=t.id,
            ticket_number=t.number,
            name=t.name,
            image=t.image,
            address=t.address,
            price=lottery.ticket_price,
            buy_available=t.owner_id is None,
        )
        for t in tickets
    ]

    return IGetNftTokensResponse(
        page=page,
        total_pages=total_pages,
        nfts=nfts
    )
    

#! Websocket router
@router.websocket("/lotteries/winners/{lottery_id}")
async def lottery_winners_websocket(websocket: WebSocket, lottery_id: int):
    try:
        token = websocket.query_params.get("token")
        if not token:
            print("Нет токена в query params")
            await websocket.close()
            return
        
        user = await get_current_user(websocket, token)
        await websocket.accept()

        from app.database.models import UserPrizes
        user_prizes = (
            await UserPrizes
            .filter(prize__lotteryprizes__lottery_id=lottery_id)
            .select_related("user")
            .select_related("prize")
        )

        winners = []
        for up in user_prizes:
            winners.append({
                "prize_id": up.prize.id,
                "title": up.prize.title,
                "user_id": up.user.id,
            })

        await websocket.send_json({"type": "winner_update", "winners": winners})
    except Exception as e:
        import traceback
        traceback.print_exc()
        await websocket.close()