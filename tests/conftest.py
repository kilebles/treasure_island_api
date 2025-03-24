import pytest_asyncio
from tortoise import Tortoise
from httpx import AsyncClient
from app.main import app
from app.config import config


@pytest_asyncio.fixture(scope="function", autouse=True)
async def initialize_tests():
    await Tortoise.init(
        db_url=config.DATABASE_URL,
        modules={"app": ["app.database.models"]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
