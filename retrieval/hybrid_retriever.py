from retrieval.dense_retriever import retrieve_chunks
from retrieval.bm25_retriever import bm25_search

def hybrid_search(query , index , bm25 , chunks , top_k = 5 , model = None): 
    dense_results = retrieve_chunks(query=query , index=index , chunks=chunks , top_k=top_k , model=model)
    bm25_results = bm25_search(query=query , bm25=bm25 , chunks=chunks , top_k=top_k)

    merged_results = []
    seen_chunks = set()
    for result in dense_results + bm25_results: 
        chunk_text = result["chunk"]
        if chunk_text not in seen_chunks: 
            merged_results.append(result)
            seen_chunks.add(chunk_text)
    return merged_results