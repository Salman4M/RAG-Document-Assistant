# RAG Document Assistant

A production-ready document question-answering API. Upload PDFs, ask questions, get answers grounded in your documents. Features full user authentication, per-user document isolation, conversation memory, and personal fact extraction.


Built from scratch without LangChain — every component implemented manually to understand the full RAG pipeline.

## Features

- **JWT Authentication** — register, login, refresh tokens, logout
- **Per-user isolation** — users can only access their own documents
- **Multi-document support** — upload and manage multiple PDFs
- **Conversation memory** — remembers previous questions automatically
- **Personal facts memory** — extracts and remembers facts you share about yourself
- **Semantic search** — finds relevant chunks using vector embeddings
- **Reranking** — cross-encoder reranker improves retrieval accuracy after vector search
- **Rate limiting** — per-user request limits (20/min on ask, 5/hour on upload)



## How It Works

1. Upload a PDF → text extracted page by page
2. Text chunked into 1000-char pieces with 200-char overlap
3. Each chunk embedded via fastembed (BAAI/bge-small-en-v1.5) and stored in ChromaDB with user_id
4. On query → question embedded → ChromaDB finds 4 most relevant chunks for that user
5. Cross-encoder reranker scores all 10 by true relevance → keeps best 4
6. Last 10 conversations + personal facts injected into system prompt
7. Qwen2.5 answers grounded in document context
8. Facts extracted from conversation and stored for future context

## Tech Stack

- **FastAPI** — REST API framework
- **PostgreSQL + SQLAlchemy** — user data, conversations, memories
- **ChromaDB** — vector database for semantic search
- **Ollama** — local LLM inference (Qwen2.5 + nomic-embed-text)
- **sentence-transformers** — cross-encoder reranking
- **pdfplumber / pypdf** — PDF text extraction
- **Alembic** — database migrations
- **Docker** — containerization

## Project Structure
```
- **FastAPI** — REST API
- **PostgreSQL + SQLAlchemy** — user data, conversations, memories
- **ChromaDB** — vector database
- **Ollama** — local LLM inference (Qwen2.5 + nomic-embed-text)
- **Alembic** — database migrations
- **Docker** — containerization

```
```
rag-document-assistant/
├── core/
│   ├── config.py          # settings
│   ├── database.py        # SQLAlchemy async engine
│   ├── security.py        # JWT + password hashing
│   └── limiter.py         # rate limiting key function

├── models/
│   └── user.py            # User, RefreshToken, Conversation, UserMemory
├── schemas/
│   └── user.py            # Pydantic schemas
├── services/
│   ├── pdf_service.py     # extraction and chunking
│   ├── ollama_service.py  # embeddings, generation, fact extraction
│   ├──  chroma_service.py  # vector store with user filtering
│   └── reranker_service.py # cross-encoder reranking
├── routes/
│   ├── routes.py          # document endpoints
│   └── auth.py            # auth endpoints
├── tests/
├── alembic/               # migrations
├── main.py
├── Dockerfile
└── docker-compose.yml
```

## Prerequisites

- [Ollama](https://ollama.ai) running locally
- Pull required models:
```bash
ollama pull qwen2.5
ollama pull nomic-embed-text
```

## Run Locally
```bash
git clone https://github.com/Salman4M/rag-document-asistant
cd rag-document-asistant
python -m venv .venv
source .venv/bin/activate
pip install -r requirements_docker.txt
```

# start PostgreSQL
docker compose up -d db

# run migrations
alembic upgrade head


# start server
uvicorn main:app --reload
```

Open http://localhost:8000/docs


## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | NO | Create account |
| POST | `/auth/login` | NO  | Get tokens |
| POST | `/auth/refresh` | NO  | Refresh access token |
| POST | `/auth/logout` |  YES | Invalidate refresh token |
| GET | `/auth/me` | YES | Current user info |
| POST | `/upload` | YES |Upload a PDF |
| GET | `/documents` | YES | List your documents |
| DELETE | `/documents/{filename}` | YES | Delete specific document |
| POST | `/ask` | YES | Ask a question |
| DELETE | `/clear` | YES | Clear all your documents |
| GET | `/health` | NO | Health check |
```

## Rate Limiting

Limits are applied per authenticated user (by user ID, not IP):

| Endpoint | Limit |
|----------|-------|
| `POST /ask` | 20 requests/minute |
| `POST /upload` | 5 requests/hour |

Exceeding the limit returns `429 Too Many Requests`.

## Tests
```bash
pytest tests/ -v
```
