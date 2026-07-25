from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_pymupdf4llm import PyMuPDF4LLMLoader


def pdf_loader(pdf_file_path : str) -> List[Document] : # return path 

    # check if path exists
    path  = Path(pdf_file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found :{pdf_file_path}")

    if path.suffix.lower() != ".pdf": 
        raise ValueError("Uploaded file is not PDF")
    loader  = PyMuPDF4LLMLoader(file_path=str(path) , mode="single")

    docs = list(loader.lazy_load())
    return docs
