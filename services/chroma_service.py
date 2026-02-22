import chromadb
from core.config import settings

client = chromadb.PersistentClient(path=settings.chroma_path)
collection = client.get_or_create_collection(name="documents")

def store_chunks(chunks:list[dict],embeddings: list[list[float]], filename:str)->int:
    ids = []
    documents = []
    metadatas = []
    embeddings_list = []

    for i, (chunk,embedding) in enumerate(zip(chunks, embeddings)):
        chunk_id = f"{filename}_{chunk['page_number']}_{chunk['chunk_index']}"
        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append({
            "filename":filename,
            "page_number":chunk["page_number"],
            "chunk_index":chunk["chunk_index"]
        })
        embeddings_list.append(embedding)

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings_list
    )

    return len(ids)

def query(question_embedding: list[float], n_results: int = None) -> list[dict]:
    #to check manually
    if n_results is None:
        n_results = settings.top_k_results
    
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=n_results
    )
    chunks = []

    for i in range(len(results["documents"][0])):
        chunks.append({
            "text":results["documents"][0][i],
            "filename":results["metadatas"][0][i]["filename"],
            "page_number":results["metadatas"][0][i]["page_number"],
            "chunk_index":results["metadatas"][0][i]["chunk_index"],
        })

    return chunks

def clear() -> None:
    global collection
    client.delete_collection(name="documents")
    collection = client.get_or_create_collection(name="documents")

def has_documents() -> bool:
    return collection.count() > 0