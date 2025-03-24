import json
from aiogram.utils import web_app
from fastapi import HTTPException, status
from tortoise.exceptions import DoesNotExist

from app.config import config
from app.database.models import User
from app.auth.jwt import create_access_token, create_refresh_token


async def login_by_init_data(init_data: str) -> dict:
    try:
        parsed_data = web_app.parse_webapp_init_data(init_data, loads=json.loads)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid init data")

    if not web_app.check_webapp_signature(config.TG_BOT_TOKEN, init_data):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid init data signature")

    tg_user = parsed_data.user

    try:
        user = await User.get(telegram_id=tg_user.id)
    except DoesNotExist:
        user = await User.create(
            telegram_id=tg_user.id,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            username=tg_user.username,
            photo=tg_user.photo,
        )

    payload = {"sub": str(user.id)}
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)

    return {
        "access": access,
        "refresh": refresh,
    }
