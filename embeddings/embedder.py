from sentence_transformers import SentenceTransformer

def load_model(): 
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2" , device="cpu")
    model.max_seq_length = 256 
    return model


def generate_embeddings(chunks , model): 

    embeddings = model.encode(chunks , batch_size = 128 , show_progress_bar = False,convert_to_numpy = True,
                              normalize_embeddings = True)

    return embeddings
