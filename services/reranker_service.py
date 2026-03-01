from sentence_transformers import CrossEncoder
import torch


_model = None

def get_reranker():
    global _model
    if _model is None:
        # device = "cuda" if torch.cuda.is_available() else "cpu"
        # _model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2",device=device)
        _model = CrossEncoder("BAAI/bge-reranker-base", device="cpu")
    return _model


def rerank(question:str, chunks: list[dict], top_k: int = 4) -> list[dict]:
    if not chunks:
        return chunks
    
    reranker = get_reranker()
    pairs = [(question,chunk["text"])for chunk in chunks]
    scores = reranker.predict(pairs)

    scored_chunks = list(zip(scores, chunks))
    scored_chunks.sort(key=lambda x: x[0],reverse=True)

    return [chunk for _, chunk in scored_chunks[:top_k]]






