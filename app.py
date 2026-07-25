import streamlit as st 
import requests
import os 

API_BASE = os.getenv("API_BASE", "http://localhost:8000") 

st.set_page_config(page_title="OmniRAG" , layout="wide")

def api_health(): 
    try: 
        r = requests.get(f"{API_BASE}/health" , timeout=3)
        return r.json() if r.ok else None
    except Exception: 
        return None

def api_ingest(file_bytes , filename): 
    try: 
        r = requests.post(f"{API_BASE}/ingest" , files={"file" : (filename , file_bytes)} , timeout=500)
        return r.json(), r.ok
    except Exception as e : 
        return {"detail":str(e)} , False
    

def api_query(query , top_k , mode , use_cache): 
    try:
        r = requests.post(
            f"{API_BASE}/query" , json = {"query" : query , "top_k" : top_k , "retrieval_mode" : mode , "use_cache" : use_cache}
            ,timeout=60
        )
        return r.json() , r.ok
    except Exception as e:
        return {"detail" : str(e)} , False


if "messages" not in st.session_state:
    st.session_state.messages = []
if "ingested" not in st.session_state:
    st.session_state.ingested = False
if "ingest_info" not in st.session_state:
    st.session_state.ingest_info = {}
if "total_queries" not in st.session_state:
    st.session_state.total_queries = 0
if "cache_hits" not in st.session_state:
    st.session_state.cache_hits = 0
 



with st.sidebar: 
    st.title("OmniRAG")
    st.caption("Hybrid Document Intelligence System")
    st.divider()

    health = api_health()
    if health is None: 
        st.error("API is Offline")
    else:
        if health.get("status") == "ok":
            st.success("API Online")
        else:
            st.warning("API degrade - Redis unavailable")
        col1 , col2 = st.columns(2)
        col1.metric("Redis" , "On" if health.get("redis") == "connected" else "Off")
        col2.metric("Chunks" , health.get("num_chunks") , 0)
    st.divider()

    st.subheader("Upload Document")
    upload = st.file_uploader("PDF , DOCX or Image" ,type=["pdf", "docx", "png", "jpg", "jpeg", "webp", "tiff"])

    if upload:
        if st.button("Ingest" , use_container_width=True , type="primary"):
            with st.spinner("Ingesting.."):
                result , ok = api_ingest(upload.getvalue() , upload.name)

            if ok:
                st.session_state.ingested = True
                st.session_state.ingest_info = result
                st.session_state.messages = []
                st.session_state.total_queries = 0
                st.session_state.cache_hits = 0
                st.success(f"Indexed {result.get('num_chunks')} chunks")
            else:
                st.error(result.get("detail", "Ingestion failed"))
    st.divider()

    st.subheader("Settings")
    mode = st.radio("Retrieval Mode" , ["hybrid" , "dense"] , 
                    captions=["BM25 + FAISS + Rerank" , "FAISS only"])
    top_k = st.slider("Top-K Chunks" , 1 , 15 , 5)
    use_cache = st.toggle("Use Redis Cache" , value=True)

    st.divider()

    st.subheader("Session States")
    col1, col2 = st.columns(2)
    col1.metric("Queries", st.session_state.total_queries)
    col2.metric("Cache Hits", st.session_state.cache_hits)

    if st.session_state.messages:
        if st.button("Clear Chat" , use_container_width=True):
            st.session_state.messages = []
            st.rerun()


st.title("OmniRAG - Document Q&A")
if not st.session_state.ingested:
    st.info("Upload and ingest a document from the sidebar to start asking questions.")
    st.stop()

info = st.session_state.ingest_info
st.caption(
    f"Active: **{info.get('file_name')}** — "
    f"{info.get('num_chunks')} chunks · {info.get('file_type', '').upper()}"
)

st.divider()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

        if msg['role'] == "assistant":
            tags = []
            if msg.get("cached"):
                tags.append("cached")
            if msg.get("mode"):
                tags.append(f"mode: {msg['mode']}")
            if tags:
                st.caption(" . ".join(tags))
            if msg.get("chunks"):
                with st.expander(f"View {len(msg["chunks"])} retrieved chunks"):
                    for i , chunk in enumerate(msg["chunks"] , 1): 
                        st.markdown(f"**Chunk {i}** — score: `{chunk.get('score', 0):.4f}`")
                        st.text(chunk.get("chunk" , "")[:400])
                        if i < len(msg["chunks"]):
                            st.divider()

query = st.chat_input("Ask a question about your document...")

if query: 
    with st.chat_message("user"):
        st.write(query)
    
    with st.chat_message("assistant"): 
        with st.spinner("Thinking..."):
            data , ok = api_query(query , top_k , mode , use_cache)
        
        st.session_state.total_queries +=1 

        if ok : 
            cached = data.get("cached" , False)
            if cached:
                st.session_state.cache_hits +=1 
            
            answer = data.get("answer" , "No answer returned")
            st.write(answer)
            tags = []
            if cached:
                tags.append("⚡ cached")
            tags.append(f"mode: {data.get('retrieval_mode', mode)}")
            st.caption(" · ".join(tags))
 
            chunks = data.get("retrieved_chunks", [])
            if chunks:
                with st.expander(f"View {len(chunks)} retrieved chunks"):
                    for i, chunk in enumerate(chunks, 1):
                        st.markdown(f"**Chunk {i}** — score: `{chunk.get('score', 0):.4f}`")
                        st.text(chunk.get("chunk", "")[:400])
                        if i < len(chunks):
                            st.divider()
            
            st.session_state.messages.append({"role" : "user" , "content" : query})
            st.session_state.messages.append({
                "role" : "assistant" , 
                "content" : answer , 
                "chunks" : chunks , 
                "cached" : cached , 
                "mode" : data.get("retrieval_mode" , mode)
            })
        
        else:
            err = data.get("detail" , "Unknown API error.")
            st.error(f"API error : {err}")
            st.session_state.messages.append({"role" : "user" , "content" : query})
            st.session_state.messages.append({
                "role" : "assistant" , 
                "content" : f"Error: {err}" , 
                "chunks" : []
            })
        st.rerun()