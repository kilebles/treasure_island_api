import pytest

from datetime import datetime, timedelta, timezone
from httpx import AsyncClient

from app.auth.jwt import create_access_token
from app.database.models import User, Lottery
from app.schemas.lottery_schema import IGetLotteriesResponse


@pytest.mark.asyncio
async def test_get_lottery_by_id_returns_correct_data(client: AsyncClient):
    user = await User.create(telegram=555, first_name="ByIdTester")
    token = create_access_token({"sub": str(user.id)})
    now = datetime.now(timezone.utc)

    main_lottery = await Lottery.create(
        name="Текущий",
        banner="main_banner", short_description="main_desc", total_sum=1000,
        event_date=now + timedelta(days=1), is_active=False,
        collection_name="main_col", collection_address="addr", collection_banner="main_col_banner",
        ticket_price=25.0
    )

    for i in range(3):
        await Lottery.create(
            name=f"Другой {i}",
            banner="b", short_description="s", total_sum=100,
            event_date=now + timedelta(days=i + 2), is_active=False,
            collection_name="col", collection_address="addr", collection_banner="cb",
            ticket_price=10.0
        )

    response = await client.get(f"/lotteries/{main_lottery.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    parsed = IGetLotteriesResponse.model_validate(response.json())
    assert parsed.activeLottery.title == "Текущий"

    assert len(parsed.activeLottery.otherLotteries) == 3
    for other in parsed.activeLottery.otherLotteries:
        assert other.title.startswith("Другой")
