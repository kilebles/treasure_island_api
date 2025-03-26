import pytest

from httpx import AsyncClient
from app.database.models import User

VALID_INIT_DATA = (
    "query_id=AAAA1&user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Admin%22%2C"
    "%22username%22%3A%22adminuser%22%7D&auth_date=1700000000&hash=securehash"
)


@pytest.mark.asyncio
async def test_admin_login_success(client: AsyncClient):
    response = await client.post(
        "/admin/login",
        data={"init_data": VALID_INIT_DATA},
    )

    assert response.status_code == 200
    data = response.json()

    assert "access" in data
    assert "refresh" in data
    assert "user" in data

    user_data = data["user"]
    assert user_data["telegramId"] == 123456789
    assert user_data["telegramUsername"] == "adminuser"
    assert user_data["telegramName"] == "Admin"

    user = await User.get_or_none(telegram=123456789)
    assert user is not None
