from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


class UserOut(BaseModel):
    id: int
    telegram_id: int
    telegram_username: Optional[str] = None
    telegram_name: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    inn: Optional[int] = None
    ton_address: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IShortUser(BaseModel):
    photo: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class IAdminShortUser(BaseModel):
    id: int
    telegram_id: int
    telegram_name: str
    telegram_username: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class InitDataLoginResponse(BaseModel):
    access: str
    refresh: str
    user: UserOut

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IBuyTokenResponse(BaseModel):
    success: bool = True
    payment_link: str

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IUpdateUserInfoRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r"^\+?\d{10,15}$")
    inn: Optional[int] = Field(None, ge=1000000000, le=9999999999999)

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True
    )


class IUpdateUserInfoResponse(BaseModel):
    success: bool = True
    user: UserOut

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IMyNftToken(BaseModel):
    id: int
    ticket_number: int
    name: str
    image: str
    address: str

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class ILotteryShortInfo(BaseModel):
    id: int
    name: str
    event_date: int

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IUserTokens(BaseModel):
    lottery: ILotteryShortInfo
    nfts: List[IMyNftToken]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class IGetMyNftTokensResponse(BaseModel):
    success: bool = True
    tokens: List[IUserTokens]

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IPrizeItem(BaseModel):
    id: int
    title: str
    description: str
    image: str
    event_date: int

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class IGetMyPrizesResponse(BaseModel):
    success: bool = True
    page: int
    total_pages: int
    prizes: List[IPrizeItem]

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )

class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )
    

class RefreshTokenResponse(BaseModel):
    access: str
    refresh: str

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )