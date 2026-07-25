from dataclasses import dataclass , field
from typing import Any , Optional

@dataclass
class IndexStore: 
    faiss_index : Optional[Any] = None
    bm25_index : Optional[Any] = None
    chunks : list[str] = field(default_factory=list)
    embed_model : Optional[Any] = None
    ocr_reader : Optional[Any] = None
    reranker : Optional[Any] = None

    @property
    def is_ready(self ) -> bool : 
        return (
            self.faiss_index is not None
            and self.bm25_index is not None
            and len(self.chunks) > 0 
        )

    def reset(self) -> None: 
        self.faiss_index = None
        self.bm25_index = None
        self.chunks = []

store = IndexStore()