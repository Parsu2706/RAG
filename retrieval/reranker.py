
def rerank_chunks(query, retrieved_chunks, top_k=5, reranker=None):

    if reranker is None:
        from sentence_transformers import CrossEncoder
        reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")  

    pairs = [
        (query, item["chunk"]) for item in retrieved_chunks
    ]
    scores = reranker.predict(pairs)

    reranked_results = [
        {
            "chunk": item["chunk"],
            "score": float(score)
        }
        for item, score in zip(retrieved_chunks, scores)
    ]

    reranked_results.sort(key=lambda x: x["score"], reverse=True)

    return reranked_results[:top_k]  