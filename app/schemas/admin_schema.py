from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.lottery_schema import LiveStatus, IPrize, IAdminLotteryInfo, \
    IAdminFullLotteryInfo
from app.schemas.users_schema import (
    ILotteryShortInfo,
    IMyNftToken,
    IPrizeItem,
    IShortUser,
    UserOut, IAdminShortUser, IAdminLotteryShortInfo
)


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
    active_lottery: Optional[IAdminLotteryShortInfo] = None
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
    active_lottery: IAdminLotteryShortInfo

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )
    

class IChangeStatusLiveRequest(BaseModel):
    live_link: Optional[str] = None

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
    

class IGetUserListResponse(BaseModel):
    success: bool = True
    page: int
    total_pages: int
    users: List[IAdminShortUser]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )
    

class IGetUserResponse(BaseModel):
    success: bool = True
    user: UserOut
    nfts: List[IMyNftToken]
    prizes: List[IPrizeItem]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )
    

class IDeleteUserResponse(IStatusResponse):
    pass


class IUpdateUserRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r"^\+?\d{10,15}$")
    inn: Optional[int] = Field(None, ge=1000000000, le=9999999999999)
    ton_address: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class IUpdateUserResponse(IStatusResponse):
    user: UserOut

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    

class IGetLotteryListResponse(IStatusResponse):
    page: int
    total_pages: int
    lotteries: List[IAdminLotteryInfo]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )
   

class IGetLotteryResponse(BaseModel):
    success: bool = True
    lottery: IAdminFullLotteryInfo

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class IUpdateLotteryRequest(BaseModel):
    name: str
    short_description: str
    banner: str
    collection_banner: str
    event_date: int
    total_sum: int
    ticket_price: float
    collection_name: str
    main_banner: str
    header_banner: str
    grand_prizes: List[IPrize]
    prizes: List[IPrize]
    tickets: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class IUpdateLotteryResponse(IStatusResponse):
    lottery: IAdminFullLotteryInfo
    

class IDeleteLotteryResponse(IStatusResponse):
    pass


class IUploadFileResponse(IStatusResponse):
    file_url: str
