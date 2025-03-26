import pytest

from httpx import AsyncClient
from app.auth.jwt import create_access_token
from app.database.models import User


@pytest.mark.asyncio
async def test_get_admin_stat(client: AsyncClient):
    user = await User.create(telegram=999999, first_name="Admin")
    token = create_access_token({"sub": str(user.id)})

    response = await client.get(
        "/admin/stat",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "success" in data
    assert data["success"] is True

    assert "activeLottery" in data
    assert "liveStatus" in data
    assert "stat" in data

    stat = data["stat"]
    assert "usersCount" in stat
    assert "ticketsEarn" in stat
    assert "activeLotteryParticipants" in stat
    assert "activeLotterySoldTicketsCount" in stat
    assert "activeLotteryTicketsCount" in stat
    assert "activeLotteryTicketsEarn" in stat
