import pytest

from datetime import datetime, timedelta, timezone
from httpx import AsyncClient

from app.auth.jwt import create_access_token
from app.database.models import User, Lottery


@pytest.mark.asyncio
async def test_get_short_lotteries_returns_only_future(client: AsyncClient):
    now = datetime.now(timezone.utc)

    user = await User.create(telegram=1111111, first_name="Admin")
    token = create_access_token({"sub": str(user.id)})

    await Lottery.create(
        name="Прошедший",
        event_date=now - timedelta(days=1),
        banner="b", short_description="s", total_sum=100,
        is_active=False,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=10.0
    )

    future = await Lottery.create(
        name="Будущий",
        event_date=now + timedelta(days=2),
        banner="b2", short_description="s2", total_sum=200,
        is_active=True,
        collection_name="col2", collection_address="addr2", collection_banner="cb2",
        ticket_price=15.0
    )

    response = await client.get(
        "/admin/lotteries/short",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert isinstance(data["lotteries"], list)
    assert len(data["lotteries"]) == 1

    lottery = data["lotteries"][0]
    assert lottery["name"] == future.name
    assert lottery["eventDate"] == int(future.event_date.timestamp())
