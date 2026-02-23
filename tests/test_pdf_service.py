import pytest
from services.pdf_service import chunk_text, extract_content_by_page


def test_chunk_text_basic():
    pages = [{"text": "a" * 2000, "page_number": 1}]
    chunks = chunk_text(pages, chunk_size=1000, overlap=200)
    assert len(chunks) > 1


def test_chunk_text_size():
    pages = [{"text": "a" * 2000, "page_number": 1}]
    chunks = chunk_text(pages, chunk_size=1000, overlap=200)
    for chunk in chunks:
        assert len(chunk["text"]) <= 1000


def test_chunk_text_overlap():
    pages = [{"text": "a" * 2000, "page_number": 1}]
    chunks = chunk_text(pages, chunk_size=1000, overlap=200)
    # second chunk should start 800 chars into first chunk's text
    assert chunks[0]["text"][800:] == chunks[1]["text"][:200]


def test_chunk_text_metadata():
    pages = [{"text": "a" * 1500, "page_number": 3}]
    chunks = chunk_text(pages, chunk_size=1000, overlap=200)
    assert chunks[0]["page_number"] == 3
    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1


def test_chunk_text_empty_page():
    pages = [{"text": "", "page_number": 1}]
    chunks = chunk_text(pages)
    assert chunks == []


def test_chunk_text_multiple_pages():
    pages = [
        {"text": "a" * 500, "page_number": 1},
        {"text": "b" * 500, "page_number": 2}
    ]
    chunks = chunk_text(pages)
    page_numbers = [c["page_number"] for c in chunks]
    assert 1 in page_numbers
    assert 2 in page_numbers


def test_extract_content_invalid_pdf():
    with pytest.raises(Exception):
        extract_content_by_page(b"not a pdf")