import pytest

from httpx import AsyncClient
from app.database.models import User, UserProfile
from app.auth.jwt import create_access_token


@pytest.mark.asyncio
async def test_get_users_returns_profiles(client: AsyncClient):
    user = await User.create(telegram=999999, first_name="Admin")
    await UserProfile.create(user=user, full_name="Админ", phone_number="+79001234567")

    token = create_access_token({"sub": str(user.id)})

    response = await client.get(
        "/admin/users/?page=1&limit=10",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["page"] == 1
    assert data["totalPages"] == 1
    assert isinstance(data["users"], list)
    assert len(data["users"]) == 1
    assert data["users"][0]["phoneNumber"] == "+79001234567"