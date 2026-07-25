from langchain_text_splitters import RecursiveCharacterTextSplitter


def recursive_chunking(text : str , chunk_size = 800 ,  chunk_overlap = 100) : 

    """ split text into chunks """
    splitter = RecursiveCharacterTextSplitter(chunk_size = chunk_size , chunk_overlap = chunk_overlap)

    chunks = splitter.split_text(text)

    return chunks