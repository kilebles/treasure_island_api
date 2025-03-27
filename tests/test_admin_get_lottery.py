import pytest

from datetime import datetime, timezone
from httpx import AsyncClient

from app.auth.jwt import create_access_token
from app.database.models import User, Lottery


@pytest.mark.asyncio
async def test_get_lottery_by_id(client: AsyncClient):
    user = await User.create(telegram=123456789, first_name="Admin")
    token = create_access_token({"sub": str(user.id)})

    lottery = await Lottery.create(
        name="Test Lottery",
        banner="banner.jpg",
        short_description="Short desc",
        total_sum=1000,
        event_date=datetime.now(timezone.utc),
        is_active=False,
        collection_name="col",
        collection_address="addr",
        collection_banner="col_banner.jpg",
        ticket_price=15.0
    )

    response = await client.get(
        f"/admin/lotteries/{lottery.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["lottery"]["name"] == "Test Lottery"
