import pytest
from fastapi.testclient import TestClient
from main import app
from services.chroma_service import clear
from unittest.mock import patch, AsyncMock, MagicMock
from core.security import create_access_token
from sqlalchemy.ext.asyncio import AsyncSession

client = TestClient(app)

TEST_USER_ID = 9999

@pytest.fixture(autouse=True)
def mock_db():
    from core.database import get_db
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(
                    all=MagicMock(return_value=[])
                )
            )
        )
    )
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    app.dependency_overrides.clear()

def get_auth_headers():
    token = create_access_token({"sub":str(TEST_USER_ID)})
    return {"Authorization":f"Bearer {token}"}

@pytest.fixture(autouse=True)
def clean_collection():
    clear(TEST_USER_ID)
    yield
    clear(TEST_USER_ID)


@pytest.fixture(autouse=True)
def mock_current_user():
    from models.user import User
    from core.security import get_current_user

    fake_user = MagicMock(spec=User)
    fake_user.id = TEST_USER_ID
    fake_user.username = "testuser"
    fake_user.email = "test@test.com"
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield fake_user
    app.dependency_overrides.clear()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_no_file():
    headers = get_auth_headers()
    response = client.post(
        "/upload",
        headers=headers
        )
    assert response.status_code == 422


def test_upload_wrong_file_type():
    headers = get_auth_headers()
    response = client.post(
        "/upload",
        files = {"file":{"test.txt",b"hello","text/plain"}},
        headers=headers
        )
    assert response.status_code == 400


def test_ask_no_document():
    headers = get_auth_headers()
    response = client.post(
        "/ask",
        json={"question": "what is this?"},
        headers=headers
        )
    assert response.status_code == 404

def test_ask_empty_question():
    headers = get_auth_headers()
    response = client.post(
        "/ask", 
        json={"question": "   "},
        headers=headers              
)
    assert response.status_code == 400


def test_clear():
    headers = get_auth_headers()
    response = client.delete("/clear",headers=headers)
    assert response.status_code == 200
    assert "message" in response.json()

def test_protected_routes_require_auth():
    app.dependency_overrides.clear()
    
    response = client.post("/upload")
    assert response.status_code == 401 or response.status_code == 422

    response = client.post("/ask",json={"question":"test"})
    assert response.status_code == 401

    response = client.delete("/clear")
    assert response.status_code == 401

