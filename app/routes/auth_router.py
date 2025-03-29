from fastapi import APIRouter, HTTPException
from app.auth.jwt import create_access_token, create_refresh_token, validate_refresh_token
from app.schemas.users_schema import RefreshTokenRequest, RefreshTokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token_handler(body: RefreshTokenRequest):
    user = await validate_refresh_token(body.refresh_token)
    payload = {"sub": str(user.id)}

    return RefreshTokenResponse(
        access=create_access_token(payload),
        refresh=create_refresh_token(payload)
    )