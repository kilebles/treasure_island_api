from fastapi import APIRouter, Depends, Form

from app.auth.dependencies import get_current_user
from app.schemas.admin_schema import IStatResponse
from app.schemas.users_schema import InitDataLoginResponse
from app.services.admin_service import get_admin_statistics
from app.services.users_service import login_by_init_data

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=InitDataLoginResponse)
async def admin_login(init_data: str = Form(...)):
    try:
        tokens = await login_by_init_data(init_data)
        return InitDataLoginResponse(**tokens)
    except Exception as e:
        raise e
    

@router.get("/stat", response_model=IStatResponse)
async def get_admin_stat(user=Depends(get_current_user)):
    return await get_admin_statistics()
