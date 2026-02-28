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


## How It Works

1. Upload a PDF → text extracted page by page
2. Text chunked into 1000-char pieces with 200-char overlap
3. Each chunk embedded via Ollama (nomic-embed-text) and stored in ChromaDB with user_id
4. On query → question embedded → ChromaDB finds 4 most relevant chunks for that user
5. Last 10 conversations + personal facts injected into system prompt
6. Qwen2.5 answers grounded in document context
7. Facts extracted from conversation and stored for future context

## Tech Stack

- **FastAPI** — REST API framework
- **PostgreSQL + SQLAlchemy** — user data, conversations, memories
- **ChromaDB** — vector database for semantic search
- **Ollama** — local LLM inference (Qwen2.5 + nomic-embed-text)
- **pdfplumber / pypdf** — PDF text extraction
- **Docker** — containerization

## Project Structure
```
- **FastAPI** — REST API
- **PostgreSQL + SQLAlchemy** — user data, conversations, memories
- **ChromaDB** — vector database
- **Ollama** — local LLM inference (Qwen2.5 + nomic-embed-text)
- **Alembic** — database migrations
- **Docker** — containerization

## Project Structure
```
rag-document-assistant/
├── core/
│   ├── config.py          # settings
│   ├── database.py        # SQLAlchemy async engine
│   └── security.py        # JWT + password hashing
├── models/
│   └── user.py            # User, RefreshToken, Conversation, UserMemory
├── schemas/
│   └── user.py            # Pydantic schemas
├── services/
│   ├── pdf_service.py     # extraction and chunking
│   ├── ollama_service.py  # embeddings, generation, fact extraction
│   └── chroma_service.py  # vector store with user filtering
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
uvicorn main:app --reload
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

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` |   | Create account |
| POST | `/auth/login` |   | Get tokens |
| POST | `/auth/refresh` |   | Refresh access token |
| POST | `/auth/logout` |   | Invalidate refresh token |
| GET | `/auth/me` |  | Current user info |
| POST | `/upload` | Upload a PDF |
| DELETE | `/documents/{filename}` |   | Delete specific document |
| POST | `/ask` | Ask a question |
| DELETE | `/clear` | Clear all your documents |
| GET | `/health` | Health check |

## Tests
```bash
pytest tests/ -v
```
