import faiss
import numpy as np 

def create_index(embeddings): 
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)
    return index



def search_similar_chunks(query_emb , index , chunks , top_k = 5): 
    dist, indices = index.search(
        np.array([query_emb]),
        top_k
)
    results = []

    for idx , distance in zip(indices[0] , dist[0]):
        results.append({
            "chunk" : chunks[idx] , 
            "distance" : float(distance)
        })
    return results

