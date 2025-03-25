import pytest
from httpx import AsyncClient
from app.database.models import User, UserProfile
from app.auth.jwt import create_access_token

@pytest.mark.asyncio
async def test_update_user_data_valid(client: AsyncClient):
    user = await User.create(telegram=12345, first_name="TestUser")
    await UserProfile.create(user=user)
    token = create_access_token({"sub": str(user.id)})

    payload = {
        "fullName": "Джорно Джованна",
        "phoneNumber": "+79001234567",
        "inn": 123456789012
    }

    response = await client.put(
        "/users/updateData",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["fullName"] == payload["fullName"]
    assert data["user"]["phoneNumber"] == payload["phoneNumber"]
    assert data["user"]["inn"] == payload["inn"]

    await user.fetch_related("profile")
    assert user.profile.full_name == payload["fullName"]
    assert user.profile.phone_number == payload["phoneNumber"]
    assert user.profile.inn == payload["inn"]


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    {"fullName": ""},
    {"phoneNumber": "not_a_number"},
    {"inn": 123},
])
async def test_update_user_data_invalid_fields(client: AsyncClient, payload):
    user = await User.create(telegram=54321, first_name="TestUserInvalid")
    await UserProfile.create(user=user)
    token = create_access_token({"sub": str(user.id)})

    response = await client.put(
        "/users/updateData",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_data_empty_payload(client: AsyncClient):
    user = await User.create(telegram=67890, first_name="TestUserEmpty")
    await UserProfile.create(user=user)
    token = create_access_token({"sub": str(user.id)})

    response = await client.put(
        "/users/updateData",
        json={},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one field must be provided"
