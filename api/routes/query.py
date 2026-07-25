import logging
import asyncio

from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, status
 
from api.cache import get_cached_query, set_cached_query
from api.index_store import store
from api.schemas import QueryRequest, QueryResponse, RetrieveChunk
 
from llm.generator import generate_response
from llm.prompt_template import build_prompt
from retrieval.dense_retriever import retrieve_chunks
from retrieval.hybrid_retriever import hybrid_search
from retrieval.reranker import rerank_chunks
 
router = APIRouter(prefix="/query", tags=["Query"])
logger = logging.getLogger(__name__)
 

_executor = ThreadPoolExecutor(max_workers=4)


@router.post("" , response_model=QueryResponse , status_code=status.HTTP_200_OK)
async def query_documents(body : QueryRequest) -> QueryResponse: 
    if not store.is_ready: 
        raise HTTPException(status_code=status.HTTP_409_CONFLICT , detail="No document has been ingested yet.")
    
    if body.use_cache: 
        cached = await get_cached_query(body.query , body.retrieval_mode , body.top_k)
        if cached: 
            cached["cached"] = True
            return QueryResponse(**cached)

    loop = asyncio.get_event_loop()

    try:
        if body.retrieval_mode == "hybrid": 
            raw_results = await loop.run_in_executor(_executor , lambda: hybrid_search(
                query=body.query , 
                index = store.faiss_index , 
                bm25=store.bm25_index , 
                chunks=store.chunks , 
                top_k=body.top_k , 
                model=store.embed_model
            ))

            results = await loop.run_in_executor(

                _executor,

                lambda: rerank_chunks(
                    query=body.query,
                    retrieved_chunks=raw_results,
                    top_k=body.top_k,
                    reranker=store.reranker,
            ))

        else:

            results = await loop.run_in_executor(

                _executor,

                lambda: retrieve_chunks(
                    query=body.query,
                    index=store.faiss_index,
                    chunks=store.chunks,
                    top_k=body.top_k,
                    model=store.embed_model,
                    
                )
            )

            for r in results:
                r.setdefault("score" , -r.get("distance" , 0.0))
                
    except Exception as e : 
        logger.exception("Retrieval failed for query: %s" , body.query)
        raise HTTPException(status_code=500 , detail=f"Retrieval error: {e}") from e
    
    chunk_texts = [r['chunk'] for r in results]
    prompt = build_prompt(query = body.query , retrieved_chunks=chunk_texts)

    try: 
        answer = await loop.run_in_executor(
            _executor , 
            generate_response , 
            prompt
        )

    except Exception as e : 
        logger.exception("LLM generation failed")
        raise HTTPException(status_code=500 , detail=f"LLM error: {e}") from e 
    retrieved_chunks = [
        RetrieveChunk(
            chunk=r["chunk"],
            score=float(r.get("score", 0.0))
        )
        for r in results
    ]
    response = QueryResponse(
        query=body.query , 
        answer=answer , 
        retrieved_chunks=retrieved_chunks , 
        retrieval_mode=body.retrieval_mode , 
        cached = False
    )

    if body.use_cache:
        await set_cached_query(
            query=body.query , 
            mode = body.retrieval_mode, 
            top_k=body.top_k , 
            response_dict=response.model_dump()
        )

    return response