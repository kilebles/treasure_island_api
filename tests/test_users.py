from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_login_by_init_data_success(monkeypatch):
    class MockUser:
        id = 123456
        first_name = "Test"
        last_name = "User"
        username = "testuser"
        photo = "http://example.com/photo.jpg"

    class MockParsedData:
        user = MockUser()

    monkeypatch.setattr(
        "app.services.users_service.web_app.parse_webapp_init_data",
        lambda data, loads=None: MockParsedData()
    )

    monkeypatch.setattr(
        "app.services.users_service.web_app.check_webapp_signature",
        lambda token, data: True
    )

    class MockDBUser:
        id = 1

    async def mock_get(*args, **kwargs):
        return MockDBUser()

    monkeypatch.setattr("app.services.users_service.User.get", mock_get)

    monkeypatch.setattr("app.services.users_service.create_access_token", lambda payload: "access123")
    monkeypatch.setattr("app.services.users_service.create_refresh_token", lambda payload: "refresh123")

    response = client.post("/users/loginByInitData", data={"init_data": "fake"})

    assert response.status_code == 200
    data = response.json()
    assert data["access"] == "access123"
    assert data["refresh"] == "refresh123"
