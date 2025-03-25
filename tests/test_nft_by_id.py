import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient

from app.auth.jwt import create_access_token
from app.database.models import User, Lottery, Ticket


@pytest.mark.asyncio
async def test_lottery_nfts_returns_correct_count(client: AsyncClient):
    user = await User.create(telegram=777, first_name="NftTester")
    token = create_access_token({"sub": str(user.id)})
    now = datetime.now(timezone.utc)

    lottery = await Lottery.create(
        name="NFT Розыгрыш",
        banner="b", short_description="s", total_sum=1000,
        event_date=now + timedelta(days=1), is_active=True,
        collection_name="col", collection_address="addr", collection_banner="cb",
        ticket_price=12.5
    )

    nft_count = 5
    for i in range(nft_count):
        await Ticket.create(
            lottery=lottery,
            number=i + 1,
            name=f"NFT #{i + 1}",
            image="https://example.com/image.png",
            address=f"TON{i + 1}",
            owner=None if i % 2 == 0 else user
        )

    response = await client.get(
        f"/lotteries/nfts/{lottery.id}?page=1&limit=10",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["nfts"]) == nft_count
