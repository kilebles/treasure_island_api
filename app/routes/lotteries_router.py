from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, WebSocket, WebSocketDisconnect
from tortoise.expressions import Q
from tortoise.timezone import now

from app.auth.dependencies import get_current_user
from app.database.models import Lottery
from app.database.models.lottery_prizes import LotteryPrizes
from app.database.models.ticket import Ticket
from app.schemas.lottery_schema import (
    ICheckLiveResponse,
    IFullLotteryInfo,
    IGetNftTokensResponse,
    ILotteryHistoryInfo,
    IGetLotteriesHistoryResponse,
    IMarketNftToken,
    LiveStatus, IPrize, IGetLotteryResponse
)
from app.services.lottery_service import get_available_nft_count

router = APIRouter(tags=["lotteries"], prefix="/lotteries")


@router.get("", response_model=IGetLotteryResponse)
async def get_lotteries(user=Depends(get_current_user)):
    active = await Lottery.get_or_none(is_active=True)
    if not active:
        raise HTTPException(status_code=404, detail="Active lottery not found")

    available_nft = await get_available_nft_count(active.id)
    total_nft = await LotteryPrizes.filter(lottery=active).count()

    remaining_seconds = max(0, int((active.event_date - now()).total_seconds()))

    grand_prizes = []
    prizes = []

    lottery_prizes = await LotteryPrizes.filter(lottery=active).select_related("prize")

    for lp in lottery_prizes:
        if lp.prize.type == 'grand':
            grand_prizes.append(lp)
        else:
            prizes.append(lp)

    active_data = IFullLotteryInfo(
        id=active.id,
        name=active.name,
        short_description=active.short_description,
        banner=active.banner,
        event_date=active.event_date.strftime("%d.%m.%Y %H:%M"),
        remaining_seconds=remaining_seconds,
        total_sum=active.total_sum,
        available_nft_count=available_nft,
        total_nft_count=total_nft,
        grand_prizes=[IPrize(title=lp.prize.title, image=lp.prize.image, description=lp.prize.description, quantity=lp.prize.quantity, winners=[]) for lp in grand_prizes],
        prizes=[IPrize(title=lp.prize.title, image=lp.prize.image, description=lp.prize.description, quantity=lp.prize.quantity, winners=[]) for lp in prizes],
        winners=[],
    )

    return IGetLotteryResponse(
        lottery=active_data
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
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    q: Optional[str] = None,
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
            description=l.short_description,
            banner=l.banner,
            event_date=l.event_date.strftime("%d.%m.%Y %H:%M"),
            total_nft_count=total_nft_count,
            ticket_price=l.ticket_price,
        ))

    return IGetLotteriesHistoryResponse(lotteries=result)


@router.get("/{lottery_id}", response_model=IGetLotteryResponse)
async def get_lottery_by_id(
    lottery_id: int = Path(..., ge=1),
    user=Depends(get_current_user)
):
    lottery = await Lottery.get_or_none(id=lottery_id)
    if not lottery:
        raise HTTPException(status_code=404, detail="Lottery not found")

    available_nft = await get_available_nft_count(lottery.id)
    total_nft = await LotteryPrizes.filter(lottery=lottery).count()

    remaining_seconds = max(0, int((lottery.event_date - now()).total_seconds()))

    grand_prizes = []
    prizes = []

    lottery_prizes = await LotteryPrizes.filter(lottery=lottery).select_related("prize")

    for lp in lottery_prizes:
        if lp.prize.type == 'grand':
            grand_prizes.append(lp)
        else:
            prizes.append(lp)

    lottery_data = IFullLotteryInfo(
        id=lottery.id,
        name=lottery.name,
        short_description=lottery.short_description,
        banner=lottery.banner,
        event_date=lottery.event_date.strftime("%d.%m.%Y %H:%M"),
        remaining_seconds=remaining_seconds,
        total_sum=lottery.total_sum,
        available_nft_count=available_nft,
        total_nft_count=total_nft,
        grand_prizes=[IPrize(title=lp.prize.title, image=lp.prize.image, description=lp.prize.description, quantity=lp.prize.quantity, winners=[]) for lp in grand_prizes],
        prizes=[IPrize(title=lp.prize.title, image=lp.prize.image, description=lp.prize.description, quantity=lp.prize.quantity, winners=[]) for lp in prizes],
        winners=[]
    )

    return IGetLotteryResponse(
        lottery=lottery_data
    )


@router.get("/nfts/{lottery_id}", response_model=IGetNftTokensResponse)
async def get_lottery_nfts(
    lottery_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
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