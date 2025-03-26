from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Body, Depends, Form, HTTPException, Query

from app.auth.dependencies import get_current_user
from app.database.models.lottery_prizes import LotteryPrizes
from app.database.models.ticket import Ticket
from app.database.models.user_prizes import UserPrizes
from app.database.models.users import User
from app.schemas.users_schema import (
    IBuyTokenResponse,
    IGetMyNftTokensResponse,
    IGetMyPrizesResponse,
    IMyNftToken,
    IPrizeItem,
    IUpdateUserInfoRequest,
    IUpdateUserInfoResponse,
    IUserTokens,
    InitDataLoginResponse,
    UserOut,
    ILotteryShortInfo
)
from app.services.users_service import login_by_init_data

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/loginByInitData", response_model=InitDataLoginResponse)
async def login_by_init_data_handler(init_data: str = Form(...)):
    tokens = await login_by_init_data(init_data)
    return InitDataLoginResponse(**tokens)


@router.post("/buy/{ticket_id}", response_model=IBuyTokenResponse)
async def buy_nft(ticket_id: int, user=Depends(get_current_user)):
    ticket = await Ticket.get_or_none(id=ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.owner_id is not None:
        raise HTTPException(status_code=403, detail="Ticket already sold")

    ticket.owner = user
    ticket.expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    await ticket.save()

    # TODO Generation link logic
    payment_link = f"https://fake.payment.gateway/nft/{ticket_id}?user={user.id}"

    return IBuyTokenResponse(payment_link=payment_link)


@router.put("/updateData", response_model=IUpdateUserInfoResponse)
async def update_user_data(
    data: IUpdateUserInfoRequest = Body(...),
    user: User = Depends(get_current_user)
):
    await user.fetch_related("profile")

    if not user.profile:
        raise HTTPException(status_code=400, detail="User profile not found")

    if not (data.full_name or data.phone_number or data.inn):
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    if data.full_name is not None:
        user.profile.full_name = data.full_name

    if data.phone_number is not None:
        user.profile.phone_number = data.phone_number

    if data.inn is not None:
        user.profile.inn = data.inn

    await user.profile.save()

    user_out = UserOut(
        id=user.id,
        telegram_id=user.telegram,
        telegram_username=user.username,
        telegram_name=user.first_name,
        full_name=user.profile.full_name,
        phone_number=user.profile.phone_number,
        inn=user.profile.inn,
        ton_address=user.profile.wallet_address,
    )

    return IUpdateUserInfoResponse(user=user_out)


@router.get("/nfts", response_model=IGetMyNftTokensResponse)
async def get_my_nfts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    user: User = Depends(get_current_user),
):
    offset = (page - 1) * limit

    tickets = await Ticket.filter(owner=user).select_related("lottery").offset(offset).limit(limit)

    grouped = {}
    for ticket in tickets:
        lid = ticket.lottery.id
        grouped.setdefault(lid, []).append(ticket)

    result = []
    for lottery_id, ticket_list in grouped.items():
        lottery = ticket_list[0].lottery
        nfts = [
            IMyNftToken(
                id=t.id,
                ticket_number=t.number,
                name=t.name,
                image=t.image,
                address=t.address,
            )
            for t in ticket_list
        ]

        result.append(IUserTokens(
            lottery=ILotteryShortInfo(
                id=lottery.id,
                name=lottery.name,
                event_date=int(lottery.event_date.timestamp()),
            ),
            nfts=nfts
        ))

    return IGetMyNftTokensResponse(
        tokens=result
    )


@router.get("/prizes", response_model=IGetMyPrizesResponse)
async def get_user_prizes(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    user=Depends(get_current_user)
):
    offset = (page - 1) * limit
    user_prizes = await UserPrizes.filter(user=user).select_related("prize").offset(offset).limit(limit)

    prize_ids = [up.prize_id for up in user_prizes]
    lottery_prizes = await LotteryPrizes.filter(prize_id__in=prize_ids).select_related("lottery")

    prize_to_date = {
        lp.prize_id: int(lp.lottery.event_date.timestamp())
        for lp in lottery_prizes if lp.lottery
    }

    result = []
    for up in user_prizes:
        p = up.prize
        event_date = prize_to_date.get(p.id, 0)
        result.append(IPrizeItem(
            id=p.id,
            title=p.title,
            description=p.description,
            image=p.image,
            event_date=event_date
        ))

    total = await UserPrizes.filter(user=user).count()
    total_pages = (total + limit - 1) // limit

    return IGetMyPrizesResponse(
        page=page,
        total_pages=total_pages,
        prizes=result
    )
    