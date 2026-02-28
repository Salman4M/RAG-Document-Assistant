import chromadb
from core.config import settings

client = chromadb.PersistentClient(path=settings.chroma_path)
collection = client.get_or_create_collection(name="documents")

def store_chunks(chunks:list[dict],embeddings: list[list[float]], filename:str, user_id: int)->int:
    ids = [f"{user_id}_{filename}_{chunk['chunk_index']}_page{chunk['page_number']}"for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            "filename":filename,
            "page_number":chunk["page_number"],
            "chunk_index":chunk["chunk_index"],
            "user_id":user_id
        }
        for chunk in chunks
    ]

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )

    return len(chunks)

def query(embedding: list[float],user_id: int, n_results: int = 4) -> list[dict]:    
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where={"user_id":user_id} # filter by user id
    )
    chunks = []

    for i,doc in enumerate(results["documents"][0]):
        chunks.append({
            "text":doc,
            "page_number":results["metadatas"][0][i]["page_number"],
            "filename":results["metadatas"][0][i]["filename"],
        })

    return chunks

def clear(user_id:int) -> None:
    results = collection.get(where={"user_id":user_id})
    if results["ids"]:
        collection.delete(ids=results["ids"])

def has_documents(user_id:int) -> bool:
    results = collection.get(where={"user_id":user_id})
    return len(results["ids"]) > 0