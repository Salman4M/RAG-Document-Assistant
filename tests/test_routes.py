import pytest
from fastapi.testclient import TestClient
from main import app
from services.chroma_service import clear

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_collection():
    clear()
    yield
    clear()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_no_document():
    response = client.post("/ask", json={"question": "what is this?"})
    assert response.status_code == 404


def test_ask_empty_question():
    response = client.post("/ask", json={"question": "   "})
    assert response.status_code == 400


def test_upload_no_file():
    response = client.post("/upload")
    assert response.status_code == 422


def test_upload_wrong_file_type():
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")}
    )
    assert response.status_code == 400


def test_clear():
    response = client.delete("/clear")
    assert response.status_code == 200
    assert response.json() == {"message": "Vector store cleared successfully"}