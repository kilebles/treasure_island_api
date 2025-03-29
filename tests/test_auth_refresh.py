import asyncio
import time
import pytest

from jose import jwt
from datetime import datetime, timedelta

from httpx import AsyncClient
from app.config import config
from app.database.models import User


VALID_INIT_DATA = f"query_id=AAAA1&user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Test%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3A%22testuser%22%2C%22photo_url%22%3A%22https%3A%2F%2Ft.me%2Fphoto.jpg%22%7D&auth_date={int(time.time())}&hash=securehash"


@pytest.mark.asyncio
async def test_refresh_token_returns_new_tokens(client: AsyncClient):
    login_response = await client.post(
        "/users/loginByInitData",
        data={"init_data": VALID_INIT_DATA},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    refresh_token = tokens["refresh"]

    await asyncio.sleep(1)

    refresh_response = await client.post(
        "/auth/refresh",
        json={"refreshToken": refresh_token},
    )
    assert refresh_response.status_code == 200

    new_tokens = refresh_response.json()
    assert "access" in new_tokens
    assert "refresh" in new_tokens
    assert new_tokens["access"] != tokens["access"]
    assert new_tokens["refresh"] != tokens["refresh"]


@pytest.mark.asyncio
async def test_refresh_token_with_garbage_token_returns_401(client: AsyncClient):
    response = await client.post("/auth/refresh", json={"refreshToken": "not.a.valid.token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


@pytest.mark.asyncio
async def test_refresh_token_with_expired_token_returns_401(client: AsyncClient):
    user = await User.create(
        telegram=999999999,
        first_name="Expired",
        last_name="User",
        username="expireduser",
    )

    expired_payload = {
        "sub": str(user.id),
        "exp": int((datetime.utcnow() - timedelta(minutes=1)).timestamp())
    }
    expired_token = jwt.encode(
        expired_payload,
        config.JWT_SECRET_KEY,
        algorithm=config.JWT_ALGORITHM
    )

    response = await client.post("/auth/refresh", json={"refreshToken": expired_token})
    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"
