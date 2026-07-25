import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
 
from api.cache import close_redis, get_redis
from api.index_store import store
from api.routes import health, ingest, query


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)

def _load_embed_model() : 
    from embeddings.embedder import load_model
    return load_model()

def _load_reranker(): 
    from sentence_transformers import CrossEncoder
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def _load_ocr(): 
    try: 
        import easyocr 
        return easyocr.Reader(["en"] , gpu=False , verbose=False)
    except Exception as e : 
        logger.warning("EasyOCR failed to load : %s" , e)


@asynccontextmanager
async def lifespan(app : FastAPI): 
    loop = asyncio.get_event_loop()

    logger.info("Starting OmniRAG API..")
    logger.info("Loading Embedding Model..")
    
    embed_model , reranker , ocr_reader = await asyncio.gather(
        loop.run_in_executor(_executor , _load_embed_model) , 
        loop.run_in_executor(_executor , _load_reranker) , 
        loop.run_in_executor(_executor , _load_ocr)
    )

    store.embed_model = embed_model 
    store.reranker = reranker 
    store.ocr_reader = ocr_reader
    logger.info("ALl models loaded.")

    await get_redis()
    yield
    logger.info("Shutting down OmniRAG API..")
    await close_redis()
    _executor.shutdown(wait=False)


app = FastAPI(
    title="OmniRAG API" , 
    description=(
        "Hybrid RAG backend — upload documents and ask questions. "
        "Supports PDF, DOCX, and images (OCR). "
        "Uses FAISS + BM25 retrieval with cross-encoder reranking and Gemini generation."
    ) , 
    version="0.2.0" , 
    lifespan=lifespan
    )

app.add_middleware(
    CORSMiddleware  , 
    allow_origins =["*"] , 
    allow_credentials = True , 
    allow_methods = ["*"] , 
    allow_headers = ["*"]
)

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query.router)

@app.get("/" , include_in_schema=False)
async def root(): 
    return {"message" : "OmniRAG API is running. Visit /docs for Swagger UI."}

