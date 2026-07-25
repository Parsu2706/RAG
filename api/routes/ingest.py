import asyncio
from concurrent.futures import ThreadPoolExecutor

import tempfile
import logging
from pathlib import Path
from fastapi import APIRouter , File , HTTPException , UploadFile , status

from api.cache import invalidate_query_cache
from api.index_store import store
from api.schemas import FileType , IngestResponse

from chunking.chunker import recursive_chunking
from embeddings.embedder import generate_embeddings
from embeddings.vector_store import create_index
from ingestion.docx_loader import load_docx_text

from ingestion.pdf_loader import pdf_loader
from ingestion.text_cleaner import clean_text
from retrieval.bm25_retriever import create_bm25_index

router = APIRouter(prefix="/ingest" , tags=["Ingest"])
logger = logging.getLogger(__name__)
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".webp", ".tiff"}

_executor = ThreadPoolExecutor(max_workers=4)

def detect_file_type(suffix : str) ->FileType: 
    mapping = {
        ".pdf" : FileType.pdf , 
        ".docx" : FileType.docx , 
        ".png" : FileType.image , 
        ".jpg" : FileType.image , 
        ".jpeg" : FileType.image , 
        ".webp" : FileType.image , 
        ".tiff" : FileType.image
    }
    return mapping[suffix.lower()]

def _extract_text(file_type : FileType , tmp_path : str , ocr_reader)->str:
    if file_type == FileType.pdf:
        docs = pdf_loader(tmp_path)

        return "\n".join(doc.page_content for doc in docs)
    elif file_type == FileType.docx:
        return load_docx_text(tmp_path)
    else: 
        from ingestion.ocr import ocr_extraction
        return ocr_extraction(tmp_path , reader = ocr_reader)
    

def _build_faiss(embeddings): 
    return create_index(embeddings)

def _build_bm25(chunks): 
    return create_bm25_index(chunks=chunks)


@router.post("" , response_model=IngestResponse , status_code=status.HTTP_200_OK)
async def ingest_file(file : UploadFile=File(...)) -> IngestResponse: 
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS: 
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE ,
            detail=f"Unsupported file type {suffix}. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )
    file_type = detect_file_type(suffix)

    content = await file.read()
    loop = asyncio.get_event_loop()

    def _write_tmp(): 
        with tempfile.NamedTemporaryFile(delete=False , suffix=suffix) as tmp : 
            tmp.write(content)
            return tmp.name
    tmp_path = await loop.run_in_executor(_executor , _write_tmp)

    try: 
        raw_text = await loop.run_in_executor(
            _executor , _extract_text , file_type , tmp_path , store.ocr_reader
        )
    except Exception as e : 
        logger.exception("Text extraction failed for %s" , e)
        raise HTTPException(
            status_code=422 , 
            detail=f"Extraction error: {e}"
        ) from e 
    
    finally : 
        Path(tmp_path).unlink(missing_ok=True)

    if not raw_text.strip(): 
        raise HTTPException(
            status_code=422 , 
            detail="No text could be extracted from the file"
        )
    
    cleaned = clean_text(raw_text)
    chunks = recursive_chunking(cleaned)

    if not chunks:
        raise HTTPException(
            status_code=422 , 
            detail = "Document produces zero chunks"
        )
    
    try : 
        if store.embed_model is None: 
            from embeddings.embedder import load_model
            store.embed_model = load_model()
        
        embeddings = await loop.run_in_executor(
            _executor ,
            lambda: generate_embeddings(
                chunks,
                store.embed_model
            ).astype("float32")
        )
    except Exception as e : 
        logger.exception("Embedding Failed.")
        raise HTTPException(
            status_code=422 , 
            detail = f"Embedding error : {e}"
        )


    try:
        faiss_index, bm25_index = await asyncio.gather(
            # Build FAISS in parallel
            loop.run_in_executor(_executor,_build_faiss,embeddings
            ),
            # Build BM25 in parallel
            loop.run_in_executor(_executor,_build_bm25,chunks
            ),
        )

    except Exception as e : 
        logger.exception("Index build failed")

        raise HTTPException(
            status_code=500 , 
            detail = f"Indexing Error{e}"
        ) from e 
    

    store.faiss_index = faiss_index
    store.bm25_index = bm25_index
    store.chunks = chunks

    await invalidate_query_cache()


    return IngestResponse(

        status="success",

        file_name=file.filename or "unknown",

        file_type=file_type,

        num_chunks=len(chunks),

        # ========================= UPDATED =========================
        # Cleaner response formatting
        message=f"Successfully indexed {len(chunks)} chunks from '{file.filename}'."
        # ==========================================================
    )

        