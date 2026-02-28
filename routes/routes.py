from fastapi import APIRouter, UploadFile, File, HTTPException,Depends
from pydantic import BaseModel
from core.security import get_current_user
from models.user import User

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
async def upload(
    file: UploadFile=File(...),
    current_user: User = Depends(get_current_user)
    ):
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
    stored = store_chunks(chunks, embeddings, file.filename, current_user.id)

    return {
        "message":"PDF proccessed successfully",
        "chunks_stored":stored,
        "filename":file.filename
    }

@router.post("/ask",response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    current_user: User = Depends(get_current_user)
    ):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail = "Question cannot be empty")
    if not has_documents(current_user.id):
        raise HTTPException(status_code=404, detail="No document uploaded yet")

    question_embedding = await get_embedding(request.question)
    chunks = query(question_embedding, current_user.id)
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
async def clear_documents(current_user: User =  Depends(get_current_user)):
    clear(current_user.id)
    return {"message":"Vector store cleared successfully"}


@router.get("/health")
async def health():
    return {"status": "ok"}