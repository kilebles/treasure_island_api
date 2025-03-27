import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone
from app.auth.jwt import create_access_token
from app.database.models import User, Lottery

@pytest.mark.asyncio
async def test_get_lottery_history(client: AsyncClient):
    user = await User.create(telegram=112233, first_name="Admin")
    token = create_access_token({"sub": str(user.id)})

    for i in range(2):
        await Lottery.create(
            name=f"Past Lottery {i}",
            banner="b",
            short_description="desc",
            total_sum=100,
            event_date=datetime.now(timezone.utc) - timedelta(days=i + 1),
            is_active=False,
            collection_name="col",
            collection_address="addr",
            collection_banner="cb",
            ticket_price=10.0
        )

    for i in range(2):
        await Lottery.create(
            name=f"Future Lottery {i}",
            banner="b",
            short_description="desc",
            total_sum=100,
            event_date=datetime.now(timezone.utc) + timedelta(days=i + 1),
            is_active=False,
            collection_name="col",
            collection_address="addr",
            collection_banner="cb",
            ticket_price=10.0
        )

    response = await client.get(
        "/admin/lotteries/history",
        params={"page": 1, "limit": 10},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    


    assert data["success"] is True
    assert data["page"] == 1
    assert data["totalPages"] == 1
    assert isinstance(data["lotteries"], list)
    assert len(data["lotteries"]) == 2
    assert all("Past Lottery" in l["name"] for l in data["lotteries"])

    for lottery in data["lotteries"]:
        assert "id" in lottery
        assert "name" in lottery
        assert "shortDescription" in lottery
        assert "banner" in lottery
        assert "collectionBanner" in lottery
        assert "eventDate" in lottery
