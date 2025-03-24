from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    telegramId: int
    telegramUsername: Optional[str] = None
    telegramName: str
    fullName: Optional[str] = None
    phoneNumber: Optional[str] = None
    inn: Optional[int] = None
    tonAddress: Optional[str] = None


class InitDataLoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    access: str
    refresh: str
    user: UserOut