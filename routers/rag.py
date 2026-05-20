from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas.rag import IndexResponse, RAGSearchRequest, RAGSearchResponse, ContextResponse
from services import rag_service
from services.document_service import get_document_by_id
from utils.security import require_permission

router = APIRouter(prefix="/rag", tags=["RAG - Semantic Search"])


@router.post("/index-document", response_model=IndexResponse)
def index_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("upload")),
):
    """
    Generate embeddings for a document and store them in the vector DB.
    Must be called after uploading a document before it can be semantically searched.
    """
    doc = get_document_by_id(document_id, db)

    try:
        chunks_indexed = rag_service.index_document(doc, db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

    return IndexResponse(
        document_id=document_id,
        chunks_indexed=chunks_indexed,
        message=f"Document '{doc.title}' indexed successfully with {chunks_indexed} chunks.",
    )


@router.delete("/remove-document/{document_id}")
def remove_document_embeddings(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("delete")),
):
    """Remove all embeddings for a document from the vector DB."""
    doc = get_document_by_id(document_id, db)
    rag_service.remove_document_embeddings(document_id)

    # Mark as un-indexed
    doc.is_indexed = False
    db.commit()

    return {"message": f"Embeddings for document '{doc.title}' removed successfully."}


@router.post("/search", response_model=RAGSearchResponse)
def semantic_search(
    request: RAGSearchRequest,
    current_user=Depends(require_permission("view")),
):
    """
    Perform semantic search over all indexed financial documents.

    Pipeline: query → embed → Qdrant ANN (top 20) → cross-encoder rerank → top 5

    Example body:
    ```json
    { "query": "financial risk related to high debt ratio" }
    ```
    """
    results = rag_service.semantic_search(
        query=request.query,
        top_k=request.top_k,
        pre_rerank_k=request.pre_rerank_k,
    )
    return RAGSearchResponse(query=request.query, results=results)


@router.get("/context/{document_id}", response_model=ContextResponse)
def get_document_context(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("view")),
):
    """Retrieve all stored text chunks for a specific document."""
    doc = get_document_by_id(document_id, db)
    chunks = rag_service.get_document_context(document_id)
    return ContextResponse(
        document_id=document_id,
        title=doc.title,
        chunks=chunks,
    )
