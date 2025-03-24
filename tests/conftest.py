import pytest
import pytest_asyncio

from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise

from app.main import app
from app.config import config
from unittest.mock import patch


async def truncate_tables():
    for model in Tortoise.apps["app"].values():
        await model.all().delete()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def initialize_tests():
    await Tortoise.init(
        db_url=config.DATABASE_URL,
        modules={"app": ["app.database.models"]},
    )
    await Tortoise.generate_schemas()
    await truncate_tables()
    yield
    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def mock_signature_check():
    with patch("app.services.users_service.web_app.check_webapp_signature", return_value=True):
        yield
