from pydantic import BaseModel


class RAGSearchRequest(BaseModel):
    query: str
    top_k: int = 5                     # final results after reranking
    pre_rerank_k: int = 20             # how many to fetch before reranking


class ChunkResult(BaseModel):
    document_id: str
    title: str
    company_name: str
    document_type: str
    chunk_text: str
    score: float                       # reranker score


class RAGSearchResponse(BaseModel):
    query: str
    results: list[ChunkResult]


class IndexResponse(BaseModel):
    document_id: str
    chunks_indexed: int
    message: str


class ContextResponse(BaseModel):
    document_id: str
    title: str
    chunks: list[str]
