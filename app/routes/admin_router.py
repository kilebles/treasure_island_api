from fastapi import APIRouter, Form, HTTPException, status
from app.schemas.users_schema import InitDataLoginResponse
from app.services.users_service import login_by_init_data

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=InitDataLoginResponse)
async def admin_login(init_data: str = Form(...)):
    try:
        tokens = await login_by_init_data(init_data)
        return InitDataLoginResponse(**tokens)
    except Exception as e:
        raise e