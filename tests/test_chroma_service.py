import pytest
from services.chroma_service import store_chunks, query, clear, has_documents


TEST_USER_ID = 9999

@pytest.fixture(autouse=True)
def clean_collection():
    clear(TEST_USER_ID)
    yield
    clear(TEST_USER_ID)


def make_chunks(n=1):
    return [
        {
            "text":f"This is test chunk number {i}",
            "page_number":1,
            "chunk_index":i
        }
        for i in range(n)
    ]

def make_embeddings(n=1):
    return [[0.1]*384 for _ in range(n)] #fastembed (bge-small) 384 dimensions


def test_has_documents_empty():
    assert has_documents(TEST_USER_ID) == False


def test_store_chunks_returns_count():
    chunks = make_chunks(1)
    embeddings = make_embeddings(1)
    count = store_chunks(chunks,embeddings,"test.pdf",TEST_USER_ID)
    assert count == 1


def test_has_documents_after_store():
    chunks = make_chunks(1)
    embeddings = make_embeddings(1)
    store_chunks(chunks,embeddings,"test.pdf",TEST_USER_ID)
    assert has_documents(TEST_USER_ID) == True


def test_clear_empties_collection():
    chunks = make_chunks(1)
    embeddings = make_embeddings(1)
    store_chunks(chunks, embeddings, "test.pdf",TEST_USER_ID)
    clear(TEST_USER_ID)
    assert has_documents(TEST_USER_ID) == False


def test_query_returns_results():
    chunks = make_chunks(1)
    embeddings = make_embeddings(1)
    store_chunks(chunks, embeddings, "test.pdf",TEST_USER_ID)
    results = query([0.1] * 384, TEST_USER_ID, n_results=1)
    assert len(results) == 1
    assert results[0]["text"] == "This is test chunk number 0"
    assert results[0]["filename"] == "test.pdf"

def test_user_isolation():
    chunks = make_chunks(1)
    embeddings = make_embeddings(1)
    store_chunks(chunks, embeddings, "test.pdf",TEST_USER_ID)

    assert has_documents(8888) == False