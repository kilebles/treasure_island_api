from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Body, Depends, Form, HTTPException

from app.auth.dependencies import get_current_user
from app.database.models.ticket import Ticket
from app.database.models.users import User
from app.services.users_service import login_by_init_data
from app.schemas.users_schema import IBuyTokenResponse, IUpdateUserInfoRequest, IUpdateUserInfoResponse, InitDataLoginResponse, UserOut

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
    
    #TODO Generate payment link logic
    
    payment_link = f"https://fake.payment.gateway/nft/{ticket_id}?user={user.id}"
    
    return IBuyTokenResponse(paymentLink=payment_link)


@router.put("/updateData", response_model=IUpdateUserInfoResponse)
async def update_user_data(
    data: IUpdateUserInfoRequest = Body(...),
    user: User = Depends(get_current_user)
):
    await user.fetch_related("profile")

    if not user.profile:
        raise HTTPException(status_code=400, detail="User profile not found")

    if not (data.fullName or data.phoneNumber or data.inn):
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    if data.fullName is not None:
        user.profile.full_name = data.fullName

    if data.phoneNumber is not None:
        user.profile.phone_number = data.phoneNumber

    if data.inn is not None:
        user.profile.inn = data.inn

    await user.profile.save()

    user_out = UserOut(
        id=user.id,
        telegramId=user.telegram,
        telegramUsername=user.username,
        telegramName=user.first_name,
        fullName=user.profile.full_name,
        phoneNumber=user.profile.phone_number,
        inn=user.profile.inn,
        tonAddress=user.profile.wallet_address,
    )

    return IUpdateUserInfoResponse(user=user_out)