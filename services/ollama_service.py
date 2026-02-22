import httpx
from core.config import settings

async def get_embedding(text:str) -> list[float]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/embeddings",
            json={
                "model":settings.ollama_embedding_model,
                "prompt":text
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["embedding"]
    

async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    embeddings = []
    for text in texts:
        embedding = await get_embedding(text)
        embeddings.append(embedding)
    
    return embeddings

def build_context(chunks: list[dict]) -> str:
    parts = []
    for chunk in chunks:
        header = f"Source: {chunk['filename']} | Page: {chunk['page_number']}"
        parts.append(f"{header}\n{chunk['text']}")
    return "\n\n".join(parts)


def trim_history(history: list=None) -> list:
    if history is None:
        history = []
    return history[-settings.max_history:]


async def ask(question:str, context_chunks: list[dict], history: list= [] )-> str:
    context = build_context(context_chunks)
    
    system_prompt = f"""You are an engineering document assistant.
Answer using ONLY the context provided below.
If the answer is not present in the cntext, say:
'I could not find this information in the uploaded document.'
Do not use any knowledge outside of the provided context.
Always reference the page nubmer when possible (e.g. 'According to page 4...').

Context:
{context}"""

    trimmed_history = trim_history(history)

    messages = [{"role":"system","content":system_prompt}]
    messages+=trimmed_history
    messages.append({"role":"user","content":question})

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model":settings.ollama_model,
                "messages":messages,
                "steam":False
            },timeout=120.0
            )
        response.raise_for_status()
        return response.json()["message"]["content"]