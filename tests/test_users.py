import pytest

from httpx import AsyncClient
from app.database.models import User

VALID_INIT_DATA = (
    "query_id=AAAA1&user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Test%22%2C"
    "%22last_name%22%3A%22User%22%2C%22username%22%3A%22testuser%22%2C"
    "%22photo_url%22%3A%22https%3A%2F%2Ft.me%2Fphoto.jpg%22%7D&auth_date=1700000000&hash=securehash"
)


@pytest.mark.asyncio
async def test_login_by_init_data_creates_user_and_profile(client: AsyncClient):
    response = await client.post(
        "/users/loginByInitData",
        data={"init_data": VALID_INIT_DATA},
    )

    assert response.status_code == 200
    data = response.json()

    assert "access" in data
    assert "refresh" in data

    user_data = data["user"]
    assert user_data["telegramId"] == 123456789
    assert user_data["telegramUsername"] == "testuser"
    assert user_data["telegramName"] == "Test"
    assert user_data["fullName"] is None
    assert user_data["tonAddress"] is None

    user = await User.get(telegram=123456789).prefetch_related("profile")
    assert user.profile is not None


@pytest.mark.asyncio
async def test_login_does_not_create_duplicate_user(client: AsyncClient):
    await client.post("/users/loginByInitData", data={"init_data": VALID_INIT_DATA})

    response = await client.post("/users/loginByInitData", data={"init_data": VALID_INIT_DATA})
    assert response.status_code == 200
    data = response.json()

    users = await User.filter(telegram=123456789).all()
    assert len(users) == 1

    user = users[0]
    await user.fetch_related("profile")
    assert user.profile is not None