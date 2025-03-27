from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, Form, HTTPException, Path, Query
from httpx import request

from app.auth.dependencies import get_current_user
from app.database.models.lottery import Lottery
from app.database.models.lottery_prizes import LotteryPrizes
from app.database.models.ticket import Ticket
from app.database.models.user_prizes import UserPrizes
from app.database.models.user_profile import UserProfile
from app.database.models.users import User
from app.schemas.admin_schema import (
    IChangeStatusLiveRequest, 
    IChangeStatusLiveResponse,
    IDeleteLotteryResponse,
    IDeleteUserResponse,
    IGetLotteryListResponse,
    IGetLotteryResponse, 
    IGetShortLotteriesResponse, 
    IGetUserListResponse,
    IGetUserResponse, 
    ILoginResponse, 
    ISetActiveLotteryResponse, 
    IStatResponse,
    IUpdateLotteryRequest,
    IUpdateLotteryResponse,
    IUpdateUserRequest,
    IUpdateUserResponse
)
from app.schemas.lottery_schema import IFullLotteryInfo, IGetLotteriesHistoryResponse, ILotteryHistoryInfo, ILotteryInfo, IPageRequest, LiveStatus
from app.schemas.users_schema import ILotteryShortInfo, IMyNftToken, IPrizeItem, IShortUser, UserOut
from app.services.admin_service import get_admin_statistics
from app.services.users_service import login_by_init_data

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=ILoginResponse)
async def admin_login(init_data: str = Form(...)):
    try:
        tokens = await login_by_init_data(init_data)
        return ILoginResponse(
            access_token=tokens["access"],
            refresh_token=tokens["refresh"],
            success=True
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return ILoginResponse(
            success=False,
            message="Unexpected error",
            access_token="",
            refresh_token=""
        )
    

@router.get("/stat", response_model=IStatResponse)
async def get_admin_stat(user=Depends(get_current_user)):
    return await get_admin_statistics()


@router.get("/lotteries/short", response_model=IGetShortLotteriesResponse)
async def get_short_lotteries(user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    lotteries = await Lottery.filter(event_date__gte=now).order_by("event_date")
    
    result = [
        ILotteryShortInfo(
            id=l.id,
            name=l.name,
            event_date=int(l.event_date.timestamp())
        )
        for l in lotteries
    ]

    return IGetShortLotteriesResponse(lotteries=result)


@router.put("/lotteries/setActive/{lottery_id}", response_model=ISetActiveLotteryResponse)
async def set_active_lottery(
    lottery_id: int = Path(..., ge=1),
    user=Depends(get_current_user)
):
    lottery = await Lottery.get_or_none(id=lottery_id)
    if not lottery:
        raise HTTPException(status_code=404, detail="Lottery not found")

    await Lottery.filter(is_active=True).update(is_active=False)
    lottery.is_active = True
    await lottery.save()

    return ISetActiveLotteryResponse(
        active_lottery=ILotteryShortInfo(
            id=lottery.id,
            name=lottery.name,
            event_date=int(lottery.event_date.timestamp())
        )
    )


@router.put("/changeLiveStatus", response_model=IChangeStatusLiveResponse)
async def change_live_status(req: IChangeStatusLiveRequest, user=Depends(get_current_user)):
    active = await Lottery.get_or_none(is_active=True)
    if not active:
        raise HTTPException(status_code=404, detail="Active lottery not found")
    
    if req.live_link:
        # TODO: Link transfer logic
        return IChangeStatusLiveResponse(live_status=LiveStatus.ONLINE)
    
    return IChangeStatusLiveResponse(live_status=LiveStatus.OFFLINE)


@router.get("/users/", response_model=IGetUserListResponse)
async def get_users(
    request: IPageRequest = Depends(),
    user=Depends(get_current_user)
):
    query = UserProfile.all()

    if request.q:
        query = query.filter(full_name__icontains=request.q)

    total = await query.count()
    total_pages = (total + request.limit - 1) // request.limit

    profiles = await query.prefetch_related("user") \
                          .offset((request.page - 1) * request.limit) \
                          .limit(request.limit)

    users = [
        IShortUser(
            photo=p.user.photo if p.user else None,
            full_name=p.full_name,
            phone_number=p.phone_number
        )
        for p in profiles
    ]

    return IGetUserListResponse(
        page=request.page,
        total_pages=total_pages,
        users=users
    )


@router.get("/users/{user_id}", response_model=IGetUserResponse)
async def get_user_info(user_id: int, _: User = Depends(get_current_user)):
    user = await User.get_or_none(id=user_id).prefetch_related("profile")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_out = UserOut(
        id=user.id,
        telegram_id=user.telegram,
        telegram_username=user.username,
        telegram_name=user.first_name,
        full_name=user.profile.full_name if user.profile else None,
        phone_number=user.profile.phone_number if user.profile else None,
        inn=user.profile.inn if user.profile else None,
        ton_address=user.profile.wallet_address if user.profile else None,
    )

    tickets = await Ticket.filter(owner_id=user.id).select_related("lottery")
    nfts = [
        IMyNftToken(
            id=t.id,
            ticket_number=t.number,
            name=t.name,
            image=t.image,
            address=t.address
        )
        for t in tickets
    ]

    user_prizes = await UserPrizes.filter(user_id=user.id).select_related("prize", "prize__lottery_prizes__lottery")
    prizes = []
    for up in user_prizes:
        prize = up.prize
        lottery = await LotteryPrizes.filter(prize=prize).select_related("lottery").first()
        event_date = int(lottery.lottery.event_date.timestamp()) if lottery and lottery.lottery else 0

        prizes.append(IPrizeItem(
            id=prize.id,
            title=prize.title,
            description=prize.description,
            image=prize.image,
            event_date=event_date
        ))

    return IGetUserResponse(user=user_out, nfts=nfts, prizes=prizes)


@router.delete("/users/{user_id}", response_model=IDeleteUserResponse)
async def delete_user(user_id: int, _: User = Depends(get_current_user)):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user.delete()
    return IDeleteUserResponse(success=True)


@router.put("/users/{user_id}", response_model=IUpdateUserResponse)
async def update_user(
    user_id: int,
    body: IUpdateUserRequest,
    _: User = Depends(get_current_user)
):
    user = await User.get_or_none(id=user_id).prefetch_related("profile")
    if not user or not user.profile:
        raise HTTPException(status_code=404, detail="User not found")

    user.profile.full_name = body.full_name or user.profile.full_name
    user.profile.phone_number = body.phone_number or user.profile.phone_number
    user.profile.inn = body.inn or user.profile.inn
    user.profile.wallet_address = body.ton_address or user.profile.wallet_address

    await user.profile.save()
    await user.fetch_related("profile")

    return IUpdateUserResponse(
        user=UserOut.model_validate({
            "id": user.id,
            "telegram_id": user.telegram,
            "telegram_username": user.username,
            "telegram_name": user.first_name,
            "full_name": user.profile.full_name,
            "phone_number": user.profile.phone_number,
            "inn": user.profile.inn,
            "ton_address": user.profile.wallet_address
        })
    )



@router.get("/lotteries/", response_model=IGetLotteryListResponse)
async def get_lottery_list(
    req: IPageRequest = Depends(),
    user: User = Depends(get_current_user)
):
    query = Lottery.all().order_by("-event_date")

    total = await query.count()
    total_pages = (total + req.limit - 1) // req.limit

    lotteries = await query.offset((req.page - 1) * req.limit).limit(req.limit)

    lottery_items = [
    ILotteryInfo(
        id=l.id,
        name=l.name,
        short_description=l.short_description,
        banner=l.banner,
        collection_banner=l.collection_banner,
        event_date=int(l.event_date.timestamp())
    )
    for l in lotteries
    ]

    return IGetLotteryListResponse(
        page=req.page,
        total_pages=total_pages,
        lotteries=lottery_items
    )


@router.get("/lotteries/history", response_model=IGetLotteryListResponse)
async def get_lottery_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    q: str | None = Query(None),
    user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    query = Lottery.filter(event_date__lt=now).order_by("-event_date")

    if q:
        query = query.filter(name__icontains=q)

    total = await query.count()
    total_pages = (total + limit - 1) // limit
    lotteries = await query.offset((page - 1) * limit).limit(limit)

    result: List[ILotteryInfo] = [
        ILotteryInfo(
            id=l.id,
            name=l.name,
            short_description=l.short_description,
            banner=l.banner,
            collection_banner=l.collection_banner,
            event_date=int(l.event_date.timestamp())
        )
        for l in lotteries
    ]

    return IGetLotteryListResponse(
        success=True,
        page=page,
        total_pages=total_pages,
        lotteries=result
    )


@router.get("/lotteries/{lottery_id}", response_model=IGetLotteryResponse)
async def get_lottery_by_id(
    lottery_id: int,
    _: User = Depends(get_current_user)
):
    lottery = await Lottery.get_or_none(id=lottery_id)
    if not lottery:
        raise HTTPException(status_code=404, detail="Lottery not found")

    full_info = IFullLotteryInfo(
        id=lottery.id,
        name=lottery.name,
        short_description=lottery.short_description,
        banner=lottery.banner,
        collection_banner=lottery.collection_banner,
        event_date=int(lottery.event_date.timestamp()),
        total_sum=lottery.total_sum,
        available_nft_count=0,
        total_nft_count=0,
        grand_prizes=[],
        prizes=[],
        winners=[],
        other_lotteries=[]
    )

    return IGetLotteryResponse(lottery=full_info)


@router.put("/lotteries/{lottery_id}", response_model=IUpdateLotteryResponse)
async def update_lottery(
    lottery_id: int,
    req: IUpdateLotteryRequest,
    _: User = Depends(get_current_user)
):
    lottery = await Lottery.get_or_none(id=lottery_id)
    if not lottery:
        raise HTTPException(status_code=404, detail="Lottery not found")

    lottery.name = req.name
    lottery.short_description = req.short_description
    lottery.banner = req.banner
    lottery.collection_banner = req.collection_banner
    lottery.event_date = datetime.fromtimestamp(req.event_date, tz=timezone.utc)
    lottery.total_sum = req.total_sum
    lottery.ticket_price = req.ticket_price
    lottery.collection_name = req.collection_name
    lottery.collection_address = req.collection_address

    await lottery.save()

    # TODO: LotteryPrizes relations

    return IUpdateLotteryResponse(
        success=True,
            lottery=IFullLotteryInfo(
                id=lottery.id,
                name=lottery.name,
                short_description=lottery.short_description,
                banner=lottery.banner,
                collection_banner=lottery.collection_banner,
                event_date=int(lottery.event_date.timestamp()),
                total_sum=lottery.total_sum,
                ticket_price=float(lottery.ticket_price),
                available_nft_count=0,
                total_nft_count=0,
                grand_prizes=[],
                prizes=[],
                winners=[],
                other_lotteries=[]
            )
        )
    

@router.delete("/lotteries/{lottery_id}", response_model=IDeleteLotteryResponse)
async def delete_lottery(lottery_id: int, _: User = Depends(get_current_user)):
    lottery = await Lottery.get_or_none(id=lottery_id)
    if not lottery:
        raise HTTPException(status_code=404, detail="Lottery not found")

    await lottery.delete()
    return IDeleteLotteryResponse(success=True)


