import pytest

from datetime import datetime, timedelta, timezone
from httpx import AsyncClient

from app.auth.jwt import create_access_token
from app.database.models import User, Lottery


@pytest.mark.asyncio
async def test_lottery_history_returns_only_past_lotteries(client: AsyncClient):
    user = await User.create(telegram=444, first_name="HistoryTester")
    token = create_access_token({"sub": str(user.id)})
    now = datetime.now(timezone.utc)

    for i in range(3):
        await Lottery.create(
            name=f"Прошедший {i}",
            banner="b", short_description="s", total_sum=100,
            event_date=now - timedelta(days=i + 1), is_active=False,
            collection_name="col", collection_address="addr", collection_banner="cb",
            ticket_price=10.0
        )

    await Lottery.create(
        name="Активный",
        banner="b", short_description="s", total_sum=100,
        event_date=now - timedelta(hours=1), is_active=True,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=10.0
    )

    await Lottery.create(
        name="Будущий",
        banner="b", short_description="s", total_sum=100,
        event_date=now + timedelta(days=1), is_active=False,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=10.0
    )

    response = await client.get("/lotteries/history?page=1&limit=10", headers={"Authorization": f"Bearer {token}"})
    data = response.json()

    assert response.status_code == 200
    assert data["success"] is True
    assert len(data["lotteries"]) == 3

    now_ts = int(now.timestamp())
    for lottery in data["lotteries"]:
        assert lottery["eventDate"] < now_ts
