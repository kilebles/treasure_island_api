import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient

from app.database.models import User, Prize, Lottery, LotteryPrizes, UserPrizes
from app.auth.jwt import create_access_token


@pytest.mark.asyncio
async def test_get_user_prizes_returns_correct_prizes_and_lottery_dates(client: AsyncClient):
    user = await User.create(telegram=9999, first_name="PrizeCollector")
    token = create_access_token({"sub": str(user.id)})

    now = datetime.now(timezone.utc)

    lottery_1 = await Lottery.create(
        name="Prize Lottery 1",
        banner="banner1",
        short_description="desc1",
        total_sum=1000,
        event_date=now - timedelta(days=5),
        is_active=False,
        collection_name="col1",
        collection_address="addr1",
        collection_banner="cb1",
        ticket_price=10.0
    )

    lottery_2 = await Lottery.create(
        name="Prize Lottery 2",
        banner="banner2",
        short_description="desc2",
        total_sum=800,
        event_date=now - timedelta(days=3),
        is_active=False,
        collection_name="col2",
        collection_address="addr2",
        collection_banner="cb2",
        ticket_price=15.0
    )

    prize_1 = await Prize.create(title="iPhone", type="nft", description="Smartphone", quantity=1, image="https://img1")
    prize_2 = await Prize.create(title="MacBook", type="nft", description="Laptop", quantity=1, image="https://img2")
    prize_3 = await Prize.create(title="iPad", type="nft", description="Tablet", quantity=1, image="https://img3")

    await LotteryPrizes.create(lottery=lottery_1, prize=prize_1)
    await LotteryPrizes.create(lottery=lottery_1, prize=prize_2)
    await LotteryPrizes.create(lottery=lottery_2, prize=prize_3)

    await UserPrizes.create(user=user, prize=prize_1)
    await UserPrizes.create(user=user, prize=prize_3)

    response = await client.get(
        "/users/prizes?page=1&limit=10",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["page"] == 1
    assert data["totalPages"] == 1
    assert len(data["prizes"]) == 2

    returned_ids = [p["id"] for p in data["prizes"]]
    assert prize_1.id in returned_ids
    assert prize_3.id in returned_ids

    for p in data["prizes"]:
        if p["id"] == prize_1.id:
            assert p["eventDate"] == int(lottery_1.event_date.timestamp())
        elif p["id"] == prize_3.id:
            assert p["eventDate"] == int(lottery_2.event_date.timestamp())