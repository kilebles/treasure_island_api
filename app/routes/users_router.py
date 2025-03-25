from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Form, HTTPException

from app.auth.dependencies import get_current_user
from app.database.models.ticket import Ticket
from app.services.users_service import login_by_init_data
from app.schemas.users_schema import IBuyTokenResponse, InitDataLoginResponse

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