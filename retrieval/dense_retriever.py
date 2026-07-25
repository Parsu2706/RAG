from embeddings.embedder import load_model
from embeddings.vector_store import search_similar_chunks
def retrieve_chunks(query, index, chunks, top_k, model=None):

    if model is None: 
        model = load_model()
    
    query_emb = model.encode(query , convert_to_numpy=True)
    results = search_similar_chunks(
        query_emb=query_emb , index=index , 
        chunks=chunks , top_k=top_k
    )

    return results