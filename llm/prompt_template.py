

def build_prompt(query : str , retrieved_chunks : list) -> str : 
    context = "\n\n".join(retrieved_chunks)

    prompt = f"""
    You are a helpful AI Research Assistant.

    Answer the user’s question using only the information provided below.

    If the answer cannot be found in the provided context, state:
    “I could not find the answer in the provided documents.”

    -----------------------------
    Context:
    {context}
    -----------------------------

    Question:
    {query}

    Answer:
    """
    return prompt.strip()
