
import pytest

from datetime import datetime, timezone
from httpx import AsyncClient

from app.auth.jwt import create_access_token
from app.database.models import User, Lottery


@pytest.mark.asyncio
async def test_update_lottery_success(client: AsyncClient):
    user = await User.create(telegram=999999, first_name="Admin")
    token = create_access_token({"sub": str(user.id)})

    lottery = await Lottery.create(
        name="Old Name", short_description="Old Desc", banner="b",
        collection_banner="cb", event_date=datetime.now(timezone.utc),
        total_sum=100, ticket_price=10.0,
        collection_name="Col", collection_address="Addr"
    )

    payload = {
        "name": "Updated Lottery",
        "shortDescription": "Updated Description",
        "banner": "new_banner",
        "collectionBanner": "new_cb",
        "eventDate": int(datetime.now(timezone.utc).timestamp()),
        "totalSum": 500,
        "ticketPrice": 20.0,
        "collectionName": "New Col",
        "collectionAddress": "New Addr",
        "mainBanner": "",
        "headerBanner": "",
        "grandPrizes": [],
        "prizes": []
    }

    response = await client.put(
        f"/admin/lotteries/{lottery.id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["lottery"]["name"] == "Updated Lottery"