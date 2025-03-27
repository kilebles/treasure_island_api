from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.lottery_schema import LiveStatus
from app.schemas.users_schema import ILotteryShortInfo


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


class IStatusResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class ILoginResponse(IStatusResponse):
    access_token: str
    refresh_token: str


class IStat(BaseModel):
    users_count: int
    tickets_earn: float
    active_lottery_participants: int
    active_lottery_sold_tickets_count: int
    active_lottery_tickets_count: int
    active_lottery_tickets_earn: float

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IStatResponse(BaseModel):
    success: bool = True
    active_lottery: Optional[ILotteryShortInfo] = None
    live_status: LiveStatus
    stat: IStat

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IGetShortLotteriesResponse(IStatusResponse):
    lotteries: List[ILotteryShortInfo]
    
    
class ISetActiveLotteryResponse(BaseModel):
    success: bool = True
    active_lottery: ILotteryShortInfo

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )
    

class IChangeStatusLiveRequest(BaseModel):
    live_link: str

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IChangeStatusLiveResponse(BaseModel):
    success: bool = True
    live_status: LiveStatus

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )