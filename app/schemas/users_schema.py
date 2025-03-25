from pydantic import BaseModel, ConfigDict
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

