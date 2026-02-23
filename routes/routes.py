from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from services.pdf_service import extract_content_by_page,chunk_text
from services.ollama_service import get_embeddings_batch,get_embedding,ask
from services.chroma_service import store_chunks,query,clear,has_documents
from core.config import settings


router = APIRouter()


class AskRequest(BaseModel):
    question:str
    history: list = None

class AskResponse(BaseModel):
    answer:str
    sources:list[dict]

@router.post("/upload")
async def upload(file: UploadFile=File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400,detail="Only PDF files are accepted")

    file_bytes=await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    
    pages = extract_content_by_page(file_bytes)

    if not pages:
        raise HTTPException(status_code=400, detail = "Could not extract any content from PDF")
    
    chunks = chunk_text(pages,settings.chunk_size,settings.chunk_overlap)
    texts = [chunk["text"] for chunk in chunks]
    embeddings = await get_embeddings_batch(texts)
    stored = store_chunks(chunks, embeddings, file.filename)

    return {
        "message":"PDF proccessed successfully",
        "chunks_stored":stored,
        "filename":file.filename
    }

@router.post("/ask",response_model=AskResponse)
async def ask_question(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail = "Question cannot be empty")
    if not has_documents():
        raise HTTPException(status_code=404, detail="No document uploaded yet")

    question_embedding = await get_embedding(request.question)
    chunks = query(question_embedding)
    answer = await ask(request.question,chunks,request.history or [])

    sources=[
        {
            "text":chunk["text"],
            "page":chunk["page_number"],
            "filename":chunk["filename"]

        }for chunk in chunks

    ]
    return AskResponse(answer=answer,sources=sources)

@router.delete("/clear")
async def clear_documents():
    clear()
    return {"message":"Vector store cleared successfully"}


@router.get("/health")
async def health():
    return {"status": "ok"}