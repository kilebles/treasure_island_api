import pytest

from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

from app.database.models import User, Lottery
from app.auth.jwt import create_access_token

@pytest.mark.asyncio
async def test_set_active_lottery(client: AsyncClient):
    user = await User.create(telegram=123456, first_name="Admin")
    token = create_access_token({"sub": str(user.id)})

    now = datetime.now(timezone.utc)
    l1 = await Lottery.create(
        name="L1", banner="b", short_description="s", total_sum=100,
        event_date=now + timedelta(days=1), is_active=False,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=10.0
    )
    l2 = await Lottery.create(
        name="L2", banner="b", short_description="s", total_sum=200,
        event_date=now + timedelta(days=2), is_active=True,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=20.0
    )

    response = await client.put(
        f"/admin/lotteries/setActive/{l1.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["activeLottery"]["id"] == l1.id

    await l1.refresh_from_db()
    await l2.refresh_from_db()
    assert l1.is_active is True
    assert l2.is_active is False