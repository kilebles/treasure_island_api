from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.lottery_schema import LiveStatus
from app.schemas.users_schema import ILotteryShortInfo

def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


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
