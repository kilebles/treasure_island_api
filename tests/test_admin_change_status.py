import pytest

from datetime import datetime, timedelta, timezone
from httpx import AsyncClient

from app.auth.jwt import create_access_token
from app.database.models import User, Lottery


@pytest.mark.asyncio
async def test_change_live_status_online(client: AsyncClient):
    user = await User.create(telegram=777777, first_name="Admin")
    token = create_access_token({"sub": str(user.id)})

    now = datetime.now(timezone.utc)
    await Lottery.create(
        name="Stream Lottery",
        banner="b", short_description="s", total_sum=500,
        event_date=now + timedelta(hours=2), is_active=True,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=10.0
    )

    payload = {"liveLink": "https://youtube.com/live/abc123"}
    response = await client.put(
        "/admin/changeLiveStatus",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["liveStatus"] == "online"


@pytest.mark.asyncio
async def test_change_live_status_offline(client: AsyncClient):
    user = await User.create(telegram=888888, first_name="Admin")
    token = create_access_token({"sub": str(user.id)})

    now = datetime.now(timezone.utc)
    await Lottery.create(
        name="Offline Stream",
        banner="b", short_description="s", total_sum=300,
        event_date=now + timedelta(hours=1), is_active=True,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=15.0
    )

    payload = {"liveLink": ""}
    response = await client.put(
        "/admin/changeLiveStatus",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["liveStatus"] == "offline"
