import pytest

from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

from app.auth.jwt import create_access_token
from app.database.models import User, UserProfile, Ticket, Prize, UserPrizes, Lottery, LotteryPrizes


@pytest.mark.asyncio
async def test_get_user_info_returns_correct_data(client: AsyncClient):
    user = await User.create(telegram=123123, first_name="Test")
    await UserProfile.create(user=user, full_name="Test User", phone_number="+70000000000", inn=1234567890)

    token = create_access_token({"sub": str(user.id)})

    lottery = await Lottery.create(
        name="Prize Lottery",
        banner="b", short_description="s", total_sum=100,
        event_date=datetime.now(timezone.utc) + timedelta(days=1),
        is_active=False,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=10.0
    )

    ticket = await Ticket.create(
        lottery=lottery, number=1, name="NFT 1",
        image="img.png", address="ADDR", owner=user
    )

    prize = await Prize.create(
        title="Prize", type="nft", description="desc", quantity=1, image="img.png"
    )

    await LotteryPrizes.create(lottery=lottery, prize=prize)
    await UserPrizes.create(user=user, prize=prize)

    response = await client.get(
        f"/admin/users/{user.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["user"]["telegramId"] == user.telegram
    assert data["nfts"]
    assert data["prizes"]