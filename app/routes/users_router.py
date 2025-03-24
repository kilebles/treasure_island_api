from fastapi import APIRouter, Form

from app.services.users_service import login_by_init_data
from app.schemas.users_schema import InitDataLoginResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/loginByInitData", response_model=InitDataLoginResponse)
async def login_by_init_data_handler(init_data: str = Form(...)):
    tokens = await login_by_init_data(init_data)
    return InitDataLoginResponse(**tokens)