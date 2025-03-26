import pytest

from datetime import datetime, timezone
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.database.models.lottery import Lottery
from app.database.models.lottery_prizes import LotteryPrizes
from app.database.models.prizes import Prize
from app.database.models.user_prizes import UserPrizes
from app.database.models.users import User
from app.auth.jwt import create_access_token


@pytest.mark.asyncio
async def test_ws_minimal():
    lottery_id = 1
    token = create_access_token({"sub": "1"})

    with TestClient(app) as client:
        try:
            with client.websocket_connect(f"/lotteries/winners/{lottery_id}?token={token}") as ws:
                data = ws.receive_json()
                print("Получили данные:", data)
                assert "type" in data
                assert data["type"] == "winner_update"
        except WebSocketDisconnect:
            pass


@pytest.mark.asyncio
async def test_ws_missing_token():
    lottery_id = 1
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/lotteries/winners/{lottery_id}") as ws:
                ws.receive_json()


@pytest.mark.asyncio
async def test_ws_winners_with_data():
    user = await User.create(telegram=12345, first_name="Test User")
    lottery = await Lottery.create(
        name="Lottery Test", banner="banner", short_description="desc",
        total_sum=100, event_date=datetime.now(timezone.utc),
        is_active=True, collection_name="collection",
        collection_address="addr", collection_banner="col_banner",
        ticket_price=10.0
    )
    prize = await Prize.create(title="Test Prize", type="nft", description="desc", quantity=1, image="img")
    await LotteryPrizes.create(lottery=lottery, prize=prize)
    await UserPrizes.create(user=user, prize=prize)

    token = create_access_token({"sub": str(user.id)})
    lottery_id = lottery.id

    with TestClient(app) as client:
        try:
            with client.websocket_connect(f"/lotteries/winners/{lottery_id}?token={token}") as ws:
                data = ws.receive_json()
                print("Получили данные:", data)
                assert data["type"] == "winner_update"
                assert any(w["prize_id"] == prize.id for w in data["winners"])
                assert any(w["user_id"] == user.id for w in data["winners"])
        except WebSocketDisconnect:
            pass