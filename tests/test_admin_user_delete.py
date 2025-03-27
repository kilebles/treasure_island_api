import pytest
from httpx import AsyncClient

from app.auth.jwt import create_access_token
from app.database.models import User


@pytest.mark.asyncio
async def test_delete_user_success(client: AsyncClient):
    user = await User.create(telegram=888888, first_name="Admin")
    token = create_access_token({"sub": str(user.id)})

    target = await User.create(telegram=123456, first_name="ToDelete")

    response = await client.delete(
        f"/admin/users/{target.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    deleted = await User.get_or_none(id=target.id)
    assert deleted is None