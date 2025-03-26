import pytest

from httpx import AsyncClient

from app.database.models import User
from app.database.models.user_profile import UserProfile
from app.auth.jwt import create_access_token


@pytest.mark.asyncio
async def test_check_live_status_response(client: AsyncClient):
    user = await User.create(telegram=123456, first_name="Streamer")
    await UserProfile.create(user=user)

    token = create_access_token({"sub": str(user.id)})

    response = await client.get(
        "/lotteries/status",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "offline"
    assert data["liveLink"] is None
