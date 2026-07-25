from pathlib import Path
from docx import Document


def load_docx_text(file_path : str) -> str: 

    docx_path = Path(file_path)

    if not docx_path.exists():
        raise FileNotFoundError(f"File Not Found:{file_path}")

    if docx_path.suffix.lower() != ".docx": 
        raise ValueError("Uploaded file is not a DOCX file")
    
    document = Document(docx_path)

    extracted_text = ""

    for paragraph in document.paragraphs: 
        extracted_text += paragraph.text + "\n"
    return extracted_text


