import pytest

from httpx import AsyncClient
from datetime import datetime, timezone

from app.database.models import User, Lottery
from app.auth.jwt import create_access_token


@pytest.mark.asyncio
async def test_delete_lottery_success(client: AsyncClient):
    user = await User.create(telegram=999999, first_name="Admin")
    token = create_access_token({"sub": str(user.id)})

    lottery = await Lottery.create(
        name="To be deleted",
        banner="b", short_description="desc", total_sum=100,
        event_date=datetime.now(timezone.utc),
        is_active=False,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=10.0
    )

    response = await client.delete(
        f"/admin/lotteries/{lottery.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    deleted = await Lottery.get_or_none(id=lottery.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_lottery_not_found(client: AsyncClient):
    user = await User.create(telegram=888888, first_name="Admin")
    token = create_access_token({"sub": str(user.id)})

    response = await client.delete(
        "/admin/lotteries/999999",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Lottery not found"
