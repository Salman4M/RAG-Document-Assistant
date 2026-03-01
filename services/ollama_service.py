import httpx
from core.config import settings
import json
import asyncio
from fastembed import TextEmbedding

_embed_model = None

def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _embed_model


async def get_embedding(text: str) -> list[float]:
    model = get_embed_model()
    embeddings = list(model.embed([text]))
    return embeddings[0].tolist()

async def get_embeddings_batch(texts:list[str]) -> list[list[float]]:
    model = get_embed_model()
    # # run it in thread pool so it doesn't block the event loop
    loop = asyncio.get_event_loop()
    embeddings = await loop.run_in_executor(
        None, lambda: list(model.embed(texts))
    )

    return [e.tolist()for e in embeddings]

# async def get_embedding(text:str) -> list[float]:
#     async with httpx.AsyncClient() as client:
#         response = await client.post(
#             f"{settings.ollama_base_url}/api/embeddings",
#             json={
#                 "model":settings.ollama_embedding_model,
#                 "prompt":text
#             },
#             timeout=30.0
#         )
#         response.raise_for_status()
#         return response.json()["embedding"]
    

# async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
#     embeddings = []
#     for text in texts:
#         embedding = await get_embedding(text)
#         embeddings.append(embedding)
    
#     return embeddings

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


async def ask(question:str, context_chunks: list[dict], history: list= None, memory_context: str = "" )-> str:
    if history is None:
        history = []

    context = build_context(context_chunks)
    
    system_prompt = f"""You are an engineering document assistant.
Answer using ONLY the context provided below.
If the answer is not present in the cntext, say:
'I could not find this information in the uploaded document.'
Do not use any knowledge outside of the provided context.
Always reference the page nubmer when possible (e.g. 'According to page 4...').{memory_context}

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
                "model": settings.ollama_model,
                "messages": messages,
                "stream": False,
                "options": {"num_predict": 1024}
            },
            timeout=120.0
        )
        response.raise_for_status()
        
        # parse all lines, collect full content
        full_content = ""
        print(response.text)
        for line in response.text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if "message" in data and data["message"].get("content"):
                    full_content += data["message"]["content"]
            except json.JSONDecodeError:
                continue
        
        return full_content if full_content else "I could not generate an answer."
    
# {'model': 'qwen2.5', 'created_at': '2026-02-23T13:56:32.714972504Z',
#   'message': {'role': 'assistant', 'content': 'I could not find this information in the uploaded document.'}, 'done': True, 'done_reason': 'stop', 'total_duration': 46482115639, 'load_duration': 19111339252, 'prompt_eval_count': 1953, 'prompt_eval_duration': 23648915076, 'eval_count': 12, 'eval_duration': 3551022719}


async def extract_facts(question:str, answer:str) -> list[str]:
    prompt = f"""Extract any personal facts the user shared about themselves from this conversation.
Only extract facts explicitly stated by the user, not inferred.
Return ONLY a JSON array of strings. If no personal facts found, return empty array [].
Examples of personal facts: name, job, location, preferences, goals.

User question: {question}
Assistant answer: {answer}

Return only JSON array, nothing else:"""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model":settings.ollama_model,
                "messages":[{"role":"user","content":prompt}],
                "stream":False,
                "options":{"num_predit":256}
            },
            timeout=30
        )
        response.raise_for_status()

        full_content = ""
        for line in response.text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if "message" in data and data["message"].get("content"):
                    full_content += data["message"]["content"]
            except json.JSONDecodeError:
                continue
        
        try:
            start = full_content.find("[")
            end = full_content.rfind("]") + 1
            if start == -1 or end == 0:
                return []
            facts = json.loads(full_content[start:end])
            return [f for f in facts if isinstance(f,str)]
        except Exception:
            return []
        

_embedding_semaphore = asyncio.Semaphore(10) # max 10 concurrent


#gpu batch acceleration  for embeddings
async def get_embedding_with_limit(text: str) -> list[float]:
    async with _embedding_semaphore:
        return await get_embedding(text)

async def get_emeddings_batch(texts: list[str])-> list[list[float]]:
    tasks = [get_embedding_with_limit(text) for text in texts]    
    return await asyncio.gather(*tasks)



    

