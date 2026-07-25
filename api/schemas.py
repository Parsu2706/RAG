from pydantic import BaseModel , Field
from typing import Optional , Literal
from enum import Enum


class FileType(str , Enum) : 
    pdf = "pdf"
    docx = "docx"
    image = "image"

class IngestResponse(BaseModel): 
    status : Literal["success" , "error"]
    file_name : str
    file_type : str 
    num_chunks : int 
    message : str

class QueryRequest(BaseModel): 
    query : str =  Field(..., min_length=1 , max_length=1000 , description="User Question")
    top_k  : int = Field(default=5 , ge=1 , le=20 , description="Number of chunks to retrieve")
    retrieval_mode : Literal["dense" , "hybrid"] = Field(default="hybrid" ,
        description= "dense (FAISS only) or hybrid (FAISS + BM25 + reranking)")
    use_cache : bool = Field(default=True , description="Whether to use redis cache for this query")

class RetrieveChunk(BaseModel): 
    chunk : str 
    score : float

class QueryResponse(BaseModel): 
    query : str 
    answer : str 
    retrieved_chunks : list[RetrieveChunk]
    retrieval_mode : str 
    cached : bool = False

class HealthResponse(BaseModel): 
    status : Literal["ok" , "degraded"]
    redis : Literal["connected" , "unavailable"]
    index_loaded : bool 
    num_chunks : int