from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class UserOut(BaseModel):
    id: int
    telegramId: int
    telegramUsername: Optional[str] = None
    telegramName: str
    fullName: Optional[str] = None
    phoneNumber: Optional[str] = None
    inn: Optional[int] = None
    tonAddress: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InitDataLoginResponse(BaseModel):
    access: str
    refresh: str
    user: UserOut
    
    model_config = ConfigDict(from_attributes=True)
    

class IBuyTokenResponse(BaseModel):
    success: bool = True
    paymentLink: str
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class IUpdateUserInfoRequest(BaseModel):
    fullName: Optional[str] = Field(None, min_length=2, max_length=100)
    phoneNumber: Optional[str] = Field(None, pattern=r"^\+?\d{10,15}$")
    inn: Optional[int] = Field(None, ge=1000000000, le=9999999999999)
    
    model_config = ConfigDict(extra="forbid")
    

class IUpdateUserInfoResponse(BaseModel):
    success: bool = True
    user: UserOut
    
    model_config = ConfigDict(from_attributes=True)