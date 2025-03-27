import pytest
from httpx import AsyncClient

from app.auth.jwt import create_access_token
from app.database.models import User, UserProfile


@pytest.mark.asyncio
async def test_update_user_success(client: AsyncClient):
    admin = await User.create(telegram=999999, first_name="Admin")
    token = create_access_token({"sub": str(admin.id)})

    user = await User.create(telegram=111111, first_name="Target")
    await UserProfile.create(user=user, full_name="Old Name", phone_number="+79999999999", inn=1234567890)

    payload = {
        "fullName": "New Name",
        "phoneNumber": "+71234567890",
        "inn": 9876543210,
        "tonAddress": "EQ123456789ABCDEF"
    }

    response = await client.put(
        f"/admin/users/{user.id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["fullName"] == "New Name"
    assert data["user"]["phoneNumber"] == "+71234567890"
    assert data["user"]["inn"] == 9876543210
    assert data["user"]["tonAddress"] == "EQ123456789ABCDEF"
