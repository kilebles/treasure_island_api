from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Path

from app.auth.dependencies import get_current_user
from app.database.models.lottery import Lottery
from app.schemas.admin_schema import IChangeStatusLiveRequest, IChangeStatusLiveResponse, IGetShortLotteriesResponse, ILoginResponse, ISetActiveLotteryResponse, IStatResponse
from app.schemas.lottery_schema import LiveStatus
from app.schemas.users_schema import ILotteryShortInfo
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