import pytest

from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

from app.database.models import User, UserProfile, Ticket, Lottery
from app.auth.jwt import create_access_token


@pytest.mark.asyncio
async def test_get_my_nft_tokens_returns_correct_user_and_lottery(client: AsyncClient):
    user = await User.create(telegram=8888, first_name="Holder")
    await UserProfile.create(user=user)
    token = create_access_token({"sub": str(user.id)})

    now = datetime.now(timezone.utc)

    lottery_1 = await Lottery.create(
        name="My First Lottery",
        banner="banner1",
        short_description="desc1",
        total_sum=500,
        event_date=now + timedelta(days=1),
        is_active=True,
        collection_name="col1",
        collection_address="addr1",
        collection_banner="cb1",
        ticket_price=10.0
    )

    lottery_2 = await Lottery.create(
        name="Second Lottery",
        banner="banner2",
        short_description="desc2",
        total_sum=800,
        event_date=now + timedelta(days=2),
        is_active=False,
        collection_name="col2",
        collection_address="addr2",
        collection_banner="cb2",
        ticket_price=20.0
    )

    ticket_1 = await Ticket.create(
        lottery=lottery_1,
        number=1,
        name="NFT #1",
        image="https://img1",
        address="TON1",
        owner=user
    )

    ticket_2 = await Ticket.create(
        lottery=lottery_2,
        number=2,
        name="NFT #2",
        image="https://img2",
        address="TON2",
        owner=user
    )

    other_user = await User.create(telegram=9999, first_name="Other")
    await Ticket.create(
        lottery=lottery_1,
        number=3,
        name="NFT Foreign",
        image="https://img3",
        address="TON3",
        owner=other_user
    )

    response = await client.get(
        "/users/nfts?page=1&limit=10",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert len(data["tokens"]) == 2

    all_ticket_ids = []
    for entry in data["tokens"]:
        assert "lottery" in entry
        assert "nfts" in entry
        for nft in entry["nfts"]:
            all_ticket_ids.append(nft["id"])
            assert nft["address"].startswith("TON")
            assert nft["ticketNumber"] in [1, 2]

    assert set(all_ticket_ids) == {ticket_1.id, ticket_2.id}