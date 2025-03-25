import pytest
from app.database.models import User


@pytest.mark.asyncio
async def test_can_create_and_fetch_user():
    user = await User.create(
        telegram=987654321,
        first_name="Check",
        last_name="Connection",
        username="testconnect",
        photo="https://t.me/photo.jpg"
    )

    fetched_user = await User.get(telegram=987654321)
    assert fetched_user.username == "testconnect"
