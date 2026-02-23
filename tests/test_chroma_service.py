import pytest
from services.chroma_service import store_chunks, query, clear, has_documents


@pytest.fixture(autouse=True)
def clean_collection():
    clear()
    yield
    clear()


def test_has_documents_empty():
    assert has_documents() is False


def test_store_chunks_returns_count():
    chunks = [{"text": "hello world", "page_number": 1, "chunk_index": 0}]
    embeddings = [[0.1] * 768]
    count = store_chunks(chunks, embeddings, "test.pdf")
    assert count == 1


def test_has_documents_after_store():
    chunks = [{"text": "hello world", "page_number": 1, "chunk_index": 0}]
    embeddings = [[0.1] * 768]
    store_chunks(chunks, embeddings, "test.pdf")
    assert has_documents() is True


def test_clear_empties_collection():
    chunks = [{"text": "hello world", "page_number": 1, "chunk_index": 0}]
    embeddings = [[0.1] * 768]
    store_chunks(chunks, embeddings, "test.pdf")
    clear()
    assert has_documents() is False


def test_query_returns_results():
    chunks = [{"text": "hello world", "page_number": 1, "chunk_index": 0}]
    embeddings = [[0.1] * 768]
    store_chunks(chunks, embeddings, "test.pdf")
    results = query([0.1] * 768, n_results=1)
    assert len(results) == 1
    assert results[0]["text"] == "hello world"
    assert results[0]["filename"] == "test.pdf"
    assert results[0]["page_number"] == 1