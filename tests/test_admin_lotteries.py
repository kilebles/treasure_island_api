import pytest

from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

from app.auth.jwt import create_access_token
from app.database.models.lottery import Lottery
from app.database.models.users import User


@pytest.mark.asyncio
async def test_get_lottery_list(client: AsyncClient):
    user = await User.create(telegram=123456, first_name="Admin")
    token = create_access_token({"sub": str(user.id)})

    for i in range(3):
        await Lottery.create(
            name=f"Lottery {i}",
            banner="banner", short_description="desc", total_sum=100,
            event_date=datetime.now(timezone.utc) + timedelta(days=i),
            is_active=False,
            collection_name="col", collection_address="addr", collection_banner="cb",
            ticket_price=10.0
        )

    response = await client.get(
        "/admin/lotteries/?page=1&limit=2",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["page"] == 1
    assert data["totalPages"] == 2
    assert len(data["lotteries"]) == 2