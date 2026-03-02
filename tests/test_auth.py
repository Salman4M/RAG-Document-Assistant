import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from main import app
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


client = TestClient(app)

async def fake_refresh(obj):
    obj.id = 1 
    obj.created_at = None

@pytest.fixture(autouse=True)
def mock_db():
    from core.database import get_db
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value = None)
    mock_result.scalars = MagicMock(
        return_value = MagicMock(
            all=MagicMock(return_value=[])
        )
    )
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = fake_refresh
    mock_session.delete = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    app.dependency_overrides.clear()


def test_register_success():
    response = client.post(
        "/auth/register",
        json={
            "username":"testuser",
            "email":"test@test.com",
            "password":"testpass123"
        })
    assert response.status_code == 201

def test_register_missing_fields():
    response = client.post(
        "/auth/register",
        json={
            "username":"testuser"
        })
    assert response.status_code == 422


def test_login_invalid_credenticals():

    response = client.post(
        "/auth/login",
        data={
            "username":"wronguser",
            "password":"wrongpass"
        })
    assert response.status_code == 401

def test_login_success():
    from models.user import User
    from core.security import hash_password

    fake_user = MagicMock(spec=User)
    fake_user.id = 1
    fake_user.username = "testuser"
    fake_user.hashed_password = hash_password("testpass123")

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(
        return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=fake_user)
        )
    )
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_session

    response = client.post(
        "/auth/login", 
        data = {
            "username":"testuser",
            "password":"testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_me_requires_auth():
    response = client.get("/auth/me")
    assert response.status_code == 401

def test_me_with_valid_token():
    from models.user import User
    from core.security import create_access_token,get_current_user

    fake_user = MagicMock(spec=User)
    fake_user.id = 1
    fake_user.username = "testuser"
    fake_user.email = "test@test.com"

    app.dependency_overrides[get_current_user] = lambda: fake_user

    token = create_access_token({"sub":"1"})
    response = client.get(
        "/auth/me",
        headers={
            "Authorization":f"Bearer {token}"
        }
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


def test_logout_requires_auth():
    response = client.post(
        "/auth/logout",
        params = {"refresh_token":"sometoken"}
    )
    assert response.status_code == 401