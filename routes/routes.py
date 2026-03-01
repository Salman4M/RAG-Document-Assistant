from fastapi import APIRouter, UploadFile, File, HTTPException,Depends,Request
from pydantic import BaseModel
from core.security import get_current_user
from models.user import User,Conversation,UserMemory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from services.chroma_service import store_chunks, query, clear, has_documents, collection
from services.reranker_service import rerank
from services.pdf_service import extract_content_by_page,chunk_text
from services.ollama_service import get_embeddings_batch,get_embedding,ask,extract_facts
from services.chroma_service import store_chunks,query,clear,has_documents
from core.config import settings
from core.limiter import limiter
import asyncio



router = APIRouter()


class AskRequest(BaseModel):
    question:str

class AskResponse(BaseModel):
    answer:str
    sources:list[dict]

@router.post("/upload")
@limiter.limit("5/hour")
async def upload(
    request: Request,
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
    stored = await asyncio.to_thread(store_chunks,chunks, embeddings, file.filename, current_user.id)

    return {
        "message":"PDF proccessed successfully",
        "chunks_stored":stored,
        "filename":file.filename
    }



@router.post("/ask",response_model=AskResponse)
@limiter.limit("20/minute")
async def ask_question(
    request: Request,
    request_body: AskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
    ):
    if not request_body.question.strip():
        raise HTTPException(status_code=400, detail = "Question cannot be empty")
    if not await asyncio.to_thread(has_documents,current_user.id):
        raise HTTPException(status_code=404, detail="No document uploaded yet")

    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id==current_user.id)
        .order_by(Conversation.created_at.desc())
        .limit(10)
    )
    past = result.scalars().all()

    history = []
    for conv in reversed(past):
        history.append({"role":"user","content":conv.question})
        history.append({"role":"assistant","content":conv.answer})

    mm_result = await db.execute(
        select(UserMemory)
        .where(UserMemory.user_id==current_user.id)
        .order_by(UserMemory.created_at.desc())
        .limit(20)
        )
    memories = mm_result.scalars().all()
    memory_context = ""
    if memories:
        facts = "\n".join(f"- {m.fact}" for m in memories)
        memory_context = f"\n\nPersonal facts about the user: \n{facts}"

    question_embedding = await get_embedding(request_body.question)
    chunks = await asyncio.to_thread(query,question_embedding, current_user.id, n_results=10) 
    chunks = rerank(request_body.question, chunks, top_k=4)  # rerank down to 4
    answer = await ask(request_body.question,chunks,history,memory_context)

    db.add(Conversation(
        user_id=current_user.id,
        question=request_body.question,
        answer=answer
    ))

    facts = await extract_facts(request_body.question, answer)
    for fact in facts:
        db.add(UserMemory(user_id=current_user.id,fact=fact))

    await db.commit()

    sources=[
        {
            "text":chunk["text"],
            "page":chunk["page_number"],
            "filename":chunk["filename"]

        }for chunk in chunks

    ]
    return AskResponse(answer=answer,sources=sources)


@router.get("/documents")
@limiter.limit("5/hour")
async def list_documents(request:Request,current_user: User = Depends(get_current_user)):
    results = await asyncio.to_thread(collection.get,where={"user_id":current_user.id})
    if not results["ids"]:
        return {"documents":[]}

    filenames = list(set(m["filename"] for m in results["metadatas"]))
    return {"documents":filenames}


@router.delete("/documents/{filename}")
async def delete_document(
    filename:str,
    current_user: User = Depends(get_current_user)
):
    results = await asyncio.to_thread(collection.get,where={
        "$and":[
            {"user_id":current_user.id},
            {"filename":filename}
        ]
    }
    )
    if not results["ids"]:
        raise HTTPException(status_code=404,detail="Document not found")
    
    await asyncio.to_thread(collection.delete,ids=results["ids"])
    return {"message": f"{filename} deleted successfully"}

@router.delete("/clear")
async def clear_documents(current_user: User =  Depends(get_current_user)):
    await asyncio.to_thread(clear,current_user.id)
    return {"message":"Vector store cleared successfully"}



@router.get("/health")
async def health():
    return {"status": "ok"}