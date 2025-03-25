import pytest

from datetime import datetime, timedelta, timezone
from httpx import AsyncClient

from app.database.models import User, Lottery, Prize, LotteryPrizes, UserPrizes
from app.schemas.lottery_schema import IGetLotteriesResponse
from app.auth.jwt import create_access_token


@pytest.mark.asyncio
async def test_lotteries_excludes_past_lottery(client: AsyncClient):
    user = await User.create(telegram=111, first_name="Test")
    token = create_access_token({"sub": str(user.id)})
    now = datetime.now(timezone.utc)
    
    await Lottery.create(
        name="Активный",
        banner="b", short_description="s", total_sum=100,
        event_date=now + timedelta(hours=1), is_active=True,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=10.0
    )

    await Lottery.create(
        name="Прошедший",
        banner="b", short_description="s", total_sum=100,
        event_date=now - timedelta(days=1), is_active=False,
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

    response = await client.get("/lotteries", headers={"Authorization": f"Bearer {token}"})
    data = response.json()
    assert response.status_code == 200
    assert "Прошедший" not in [l["name"] for l in data["futureLotteries"]]
    assert "Будущий" in [l["name"] for l in data["futureLotteries"]]


@pytest.mark.asyncio
async def test_lotteries_event_dates_are_future(client: AsyncClient):
    user = await User.create(telegram=222, first_name="FutureGuy")
    token = create_access_token({"sub": str(user.id)})
    now = int(datetime.now(timezone.utc).timestamp())

    await Lottery.create(
        name="Будущий2",
        banner="b", short_description="s", total_sum=100,
        event_date=datetime.now(timezone.utc) + timedelta(hours=1), is_active=True,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=10.0
    )

    response = await client.get("/lotteries", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    parsed = IGetLotteriesResponse.model_validate(response.json())

    assert isinstance(parsed.activeLottery.eventDate, int)
    assert parsed.activeLottery.eventDate >= now


@pytest.mark.asyncio
async def test_lotteries_available_nft_count(client: AsyncClient):
    user = await User.create(telegram=333, first_name="NFTGuy")
    token = create_access_token({"sub": str(user.id)})
    now = datetime.now(timezone.utc)

    current = await Lottery.create(
        name="NFT Test",
        banner="b", short_description="s", total_sum=100,
        event_date=now + timedelta(hours=1), is_active=True,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=10.0
    )

    p1 = await Prize.create(title="NFT1", type="nft", description="desc", quantity=1, image="url")
    p2 = await Prize.create(title="NFT2", type="nft", description="desc", quantity=1, image="url")

    await LotteryPrizes.create(lottery=current, prize=p1)
    await LotteryPrizes.create(lottery=current, prize=p2)

    await UserPrizes.create(user=user, prize=p1)

    response = await client.get("/lotteries", headers={"Authorization": f"Bearer {token}"})
    data = response.json()

    assert response.status_code == 200
    assert data["activeLottery"]["availableNftCount"] == 1
    assert data["activeLottery"]["totalNftCount"] == 2
