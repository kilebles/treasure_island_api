from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Path, Query, UploadFile
from httpx import request

from app.auth.dependencies import get_current_user
from app.database.models import Prize, Option
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
    IUpdateUserResponse, IUploadFileResponse
)
from app.schemas.lottery_schema import IFullLotteryInfo, IGetLotteriesHistoryResponse, ILotteryHistoryInfo, \
    ILotteryInfo, IPageRequest, LiveStatus, IAdminLotteryInfo, IAdminFullLotteryInfo, IPrize
from app.schemas.users_schema import ILotteryShortInfo, IMyNftToken, IPrizeItem, IShortUser, UserOut, IAdminShortUser, \
    IAdminLotteryShortInfo
from app.services.admin_service import get_admin_statistics
from app.services.file_upload import FileUpload
from app.services.lottery_service import get_available_nft_count
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
        active_lottery=IAdminLotteryShortInfo(
            id=lottery.id,
            name=lottery.name,
            event_date=int(lottery.event_date.timestamp()),
            banner=lottery.banner
        )
    )


@router.put("/changeLiveStatus", response_model=IChangeStatusLiveResponse)
async def change_live_status(req: IChangeStatusLiveRequest, user=Depends(get_current_user)):
    active = await Lottery.get_or_none(is_active=True)
    if not active:
        raise HTTPException(status_code=404, detail="Active lottery not found")

    option = await Option.get(key='liveStatus')
    if req.live_link:
        # TODO: Link transfer logic
        option.value = "1"
        await option.save()
        return IChangeStatusLiveResponse(live_status=LiveStatus.ONLINE)

    option.value = "0"
    await option.save()
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
        IAdminShortUser(
            id=p.user.id,
            telegram_id=p.user.telegram,
            telegram_username=p.user.username,
            telegram_name=p.user.full_name,
            photo=p.user.photo,
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

    lotteries = await query.offset((req.page - 1) * req.limit).limit(req.limit).prefetch_related("tickets")

    lottery_items = [
        IAdminLotteryInfo(
            id=l.id,
            title=l.name,
            event_date=int(l.event_date.timestamp()),
            total_nft_count=len(l.tickets),
            nft_cost=l.ticket_price
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
        q: Optional[str] = Query(None),
        user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    query = Lottery.filter(event_date__lt=now).order_by("-event_date")

    if q:
        query = query.filter(name__icontains=q)

    total = await query.count()
    total_pages = (total + limit - 1) // limit
    lotteries = await query.offset((page - 1) * limit).limit(limit).prefetch_related("tickets")

    result: List[IAdminLotteryInfo] = [
        IAdminLotteryInfo(
            id=l.id,
            title=l.name,
            event_date=int(l.event_date.timestamp()),
            total_nft_count=len(l.tickets),
            nft_cost=l.ticket_price
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

    available_nft_count = await get_available_nft_count(lottery.id)
    total_nft_count = await LotteryPrizes.filter(lottery=lottery).count()

    grand_prizes = []
    prizes = []

    lottery_prizes = await LotteryPrizes.filter(lottery=lottery).select_related("prize")

    for lp in lottery_prizes:
        if lp.prize.type == 'grand':
            grand_prizes.append(
                IPrize(
                    title=lp.prize.title,
                    image=lp.prize.image,
                    description=lp.prize.description,
                    quantity=lp.prize.quantity,
                    winners=[]
                )
            )
        else:
            prizes.append(
                IPrize(
                    title=lp.prize.title,
                    image=lp.prize.image,
                    description=lp.prize.description,
                    quantity=lp.prize.quantity,
                    winners=[]
                )
            )

    full_info = IAdminFullLotteryInfo(
        id=lottery.id,
        name=lottery.name,
        short_description=lottery.short_description,
        banner=lottery.banner,
        header_banner=lottery.header_banner,
        main_banner=lottery.main_banner,
        collection_banner=lottery.collection_banner,
        collection_name=lottery.collection_name,
        event_date=int(lottery.event_date.timestamp()),
        ticket_price=lottery.ticket_price,
        total_sum=lottery.total_sum,
        available_nft_count=available_nft_count,
        total_nft_count=total_nft_count,
        grand_prizes=grand_prizes,
        prizes=prizes,
        winners=[],
        other_lotteries=[]
    )

    return IGetLotteryResponse(lottery=full_info)


@router.post("/lotteries/", response_model=IUpdateLotteryResponse)
async def create_lottery(
        req: IUpdateLotteryRequest,
        _: User = Depends(get_current_user)
):
    lottery = await Lottery.create(
        name=req.name,
        short_description=req.short_description,
        banner=req.banner,
        header_banner=req.header_banner,
        main_banner=req.main_banner,
        collection_banner=req.collection_banner,
        event_date=datetime.fromtimestamp(req.event_date, tz=timezone.utc),
        total_sum=req.total_sum,
        ticket_price=req.ticket_price,
        collection_name=req.collection_name,
    )
    prizes = []
    grand_prizes = []

    for pr in req.grand_prizes:
        prize = await Prize.create(
            title=pr.title,
            type='grand',
            image=pr.image,
            description=pr.description,
            quantity=pr.quantity
        )
        await LotteryPrizes.create(
            lottery_id=lottery.id,
            prize_id=prize.id
        )
        grand_prizes.append(
            IPrize(
                title=pr.title,
                image=pr.image,
                description=pr.description,
                quantity=pr.quantity,
                winners=[]
            )
        )

    for pr in req.prizes:
        prize = await Prize.create(
            title=pr.title,
            type='common',
            image=pr.image,
            description=pr.description,
            quantity=pr.quantity
        )
        await LotteryPrizes.create(
            lottery_id=lottery.id,
            prize_id=prize.id
        )
        prizes.append(
            IPrize(
                title=pr.title,
                image=pr.image,
                description=pr.description,
                quantity=pr.quantity,
                winners=[]
            )
        )

    return IUpdateLotteryResponse(
        success=True,
        lottery=IAdminFullLotteryInfo(
            id=lottery.id,
            name=lottery.name,
            short_description=lottery.short_description,
            banner=lottery.banner,
            header_banner=lottery.header_banner,
            main_banner=lottery.main_banner,
            collection_banner=lottery.collection_banner,
            collection_name=lottery.collection_name,
            event_date=int(lottery.event_date.timestamp()),
            total_sum=lottery.total_sum,
            ticket_price=float(lottery.ticket_price),
            available_nft_count=0,
            total_nft_count=0,
            grand_prizes=[],
            prizes=prizes,
            winners=grand_prizes,
            other_lotteries=[]
        )
    )


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
    lottery.header_banner = req.header_banner
    lottery.main_banner = req.main_banner
    lottery.collection_banner = req.collection_banner
    lottery.collection_name = req.collection_name
    lottery.event_date = datetime.fromtimestamp(req.event_date, tz=timezone.utc)
    lottery.total_sum = req.total_sum
    lottery.ticket_price = req.ticket_price
    lottery.collection_name = req.collection_name

    await lottery.save()

    # TODO: LotteryPrizes relations
    grand_prizes = []
    prizes = []

    await Prize.filter(lottery=lottery).delete()

    for pr in req.grand_prizes:
        prize = await Prize.get_or_none(id=pr.id)
        if not prize:
            raise HTTPException(status_code=404, detail="Prize not found")
        prize.title = pr.title
        prize.image = pr.image
        prize.description = pr.description
        prize.quantity = pr.quantity
        await prize.save()

        grand_prizes.append(
            IPrize(
                title=pr.title,
                image=pr.image,
                description=pr.description,
                quantity=pr.quantity,
                winners=[]
            )
        )

    for pr in req.prizes:
        prize = await Prize.get_or_none(id=pr.id)
        if not prize:
            raise HTTPException(status_code=404, detail="Prize not found")
        prize.title = pr.title
        prize.image = pr.image
        prize.description = pr.description
        prize.quantity = pr.quantity
        await prize.save()

        prizes.append(
            IPrize(
                title=pr.title,
                image=pr.image,
                description=pr.description,
                quantity=pr.quantity,
                winners=[]
            )
        )

    return IUpdateLotteryResponse(
        success=True,
        lottery=IAdminFullLotteryInfo(
            id=lottery.id,
            name=lottery.name,
            short_description=lottery.short_description,
            banner=lottery.banner,
            header_banner=lottery.header_banner,
            main_banner=lottery.main_banner,
            collection_banner=lottery.collection_banner,
            collection_name=lottery.collection_name,
            event_date=int(lottery.event_date.timestamp()),
            total_sum=lottery.total_sum,
            ticket_price=float(lottery.ticket_price),
            available_nft_count=0,
            total_nft_count=0,
            grand_prizes=grand_prizes,
            prizes=prizes,
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


@router.post("/upload", response_model=IUploadFileResponse)
async def upload_lottery_banner(file: UploadFile, _: User = Depends(get_current_user)):
    upload = FileUpload()
    file_url = await upload.upload(file)
    return IUploadFileResponse(file_url=file_url)
