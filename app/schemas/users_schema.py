from pydantic import BaseModel
from fastapi import Form


class InitDataLoginRequest(BaseModel):
    def __init__(self, init_data: str = Form(...)):
        self.init_data = init_data
    

class InitDataLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    # token_type: str = "bearer"