from enum import Enum

from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.users_schema import IShortUser


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


class ILotteryInfo(BaseModel):
    id: int
    name: str
    short_description: str
    banner: str
    collection_banner: str
    event_date: int

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IAdminLotteryInfo(BaseModel):
    id: int
    title: str
    event_date: int
    total_nft_count: int
    nft_cost: int

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IPrize(BaseModel):
    title: str
    image: str
    description: str
    quantity: int
    winners: List[IShortUser]

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IFullLotteryInfo(ILotteryInfo):
    total_sum: int
    available_nft_count: int
    total_nft_count: int
    grand_prizes: list[IPrize] = []
    prizes: list[IPrize] = []
    winners: list[IShortUser] = []
    tickets: Optional[str] = None
    other_lotteries: list[ILotteryInfo] = []

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IGetLotteriesResponse(BaseModel):
    success: bool = True
    active_lottery: IFullLotteryInfo
    future_lotteries: list[ILotteryInfo]

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IPageRequest(BaseModel):
    page: int
    limit: int = 10
    q: str | None = None


class ILotteryHistoryInfo(BaseModel):
    id: int
    name: str
    event_date: int
    total_nft_count: int
    ticket_price: float

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IGetLotteriesHistoryResponse(BaseModel):
    success: bool = True
    lotteries: list[ILotteryHistoryInfo]

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IMarketNftToken(BaseModel):
    id: int
    ticket_number: int
    name: str
    image: str
    address: str
    price: float
    buy_available: bool

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IGetNftTokensResponse(BaseModel):
    success: bool = True
    page: int
    total_pages: int
    nfts: list[IMarketNftToken]

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IGetNftTokensRequest(BaseModel):
    page: int = 1
    limit: int = 10
    min_number: int | None = None
    max_number: int | None = None


class LiveStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class ICheckLiveResponse(BaseModel):
    success: bool = True
    status: LiveStatus
    live_link: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class WinnerItem(BaseModel):
    prize_id: int
    title: str
    user_id: int
    

class WinnerUpdate(BaseModel):
    type: str = "winner_update"
    winners: List[WinnerItem]
    