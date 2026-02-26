# RAG Document Assistant

A document question-answering API built with FastAPI. Upload a PDF, ask questions about it, get answers grounded in the document content.

Built from scratch without LangChain — every component implemented manually to understand the full RAG pipeline.

## How It Works

1. Upload a PDF → text extracted page by page
2. Text chunked into 1000-char pieces with 200-char overlap
3. Each chunk converted to a vector embedding via Ollama (nomic-embed-text)
4. Embeddings stored in ChromaDB vector database
5. On query → question embedded → ChromaDB finds 4 most relevant chunks
6. Chunks + question sent to Qwen2.5 with a grounded system prompt
7. Answer returned with source references

## Tech Stack

- **FastAPI** — REST API framework
- **ChromaDB** — vector database for semantic search
- **Ollama** — local LLM inference (Qwen2.5 + nomic-embed-text)
- **pdfplumber / pypdf** — PDF text extraction
- **Docker** — containerization

## Project Structure
```
rag-document-assistant/
├── core/
│   └── config.py          # settings via pydantic
├── services/
│   ├── pdf_service.py     # extraction and chunking
│   ├── ollama_service.py  # embeddings and generation
│   └── chroma_service.py  # vector store operations
├── routes/
│   └── routes.py          # API endpoints
├── tests/                 # 18 passing tests
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

Open http://localhost:8000/docs

## Run with Docker
```bash
docker compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload a PDF |
| POST | `/ask` | Ask a question |
| DELETE | `/clear` | Clear vector store |
| GET | `/health` | Health check |

## Tests
```bash
pytest tests/ -v
```

18 tests covering pdf_service, chroma_service, and routes.