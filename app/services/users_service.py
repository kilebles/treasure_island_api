import json

from aiogram.utils import web_app
from fastapi import HTTPException, status

from app.config import config
from app.database.models import User, UserProfile
from app.auth.jwt import create_access_token, create_refresh_token


async def login_by_init_data(init_data: str) -> dict:
    try:
        parsed_data = web_app.parse_webapp_init_data(init_data, loads=json.loads)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid init data"
        )

    if not web_app.check_webapp_signature(config.TG_BOT_TOKEN, init_data):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid init data signature"
        )

    tg_user = parsed_data.user
    user = await User.filter(telegram=tg_user.id).select_related("profile").first()

    if not user:
        user = await User.create(
            telegram=tg_user.id,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            username=tg_user.username,
            photo=tg_user.photo,
        )

        await UserProfile.create(user=user)
        await user.fetch_related("profile")

    user_data = {
        "id": user.id,
        "telegramId": user.telegram,
        "telegramUsername": user.username,
        "telegramName": user.first_name,
        "fullName": user.profile.full_name if user.profile else None,
        "phoneNumber": user.profile.phone_number if user.profile else None,
        "inn": user.profile.inn if user.profile else None,
        "tonAddress": user.profile.wallet_address if user.profile else None,
    }

    payload = {"sub": str(user.id)}
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)

    return {
        "access": access,
        "refresh": refresh,
        "user": user_data,
    }
