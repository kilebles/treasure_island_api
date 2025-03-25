import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from app.auth.jwt import create_access_token
from app.database.models import User, Lottery, Ticket


@pytest.mark.asyncio
async def test_buy_nft_assigns_owner_and_sets_expires_at(client: AsyncClient):
    user = await User.create(telegram=888, first_name="Buyer")
    token = create_access_token({"sub": str(user.id)})
    now = datetime.now(timezone.utc)

    lottery = await Lottery.create(
        name="BuyTest", banner="b", short_description="s", total_sum=100,
        event_date=now + timedelta(days=1), is_active=True,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=10.0
    )

    ticket = await Ticket.create(
        lottery=lottery,
        number=1,
        name="NFT #1",
        image="https://image",
        address="TON1",
        owner=None
    )

    response = await client.post(
        f"/users/buy/{ticket.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["paymentLink"].startswith("https://")

    await ticket.refresh_from_db()
    assert ticket.owner_id == user.id

    assert ticket.expires_at is not None
    delta_minutes = (ticket.expires_at - datetime.now(timezone.utc)).total_seconds() / 60
    assert 14 <= delta_minutes <= 15.1
