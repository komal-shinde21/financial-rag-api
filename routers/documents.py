from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas.document import DocumentOut, DocumentType
from services import document_service
from utils.security import get_current_user, require_permission

router = APIRouter(prefix="/documents", tags=["Documents"])


def _to_out(doc) -> DocumentOut:
    return DocumentOut(
        document_id=doc.id,
        title=doc.title,
        company_name=doc.company_name,
        document_type=doc.document_type,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
        is_indexed=doc.is_indexed,
    )


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    title: str = Form(...),
    company_name: str = Form(...),
    document_type: DocumentType = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("upload")),
):
    """Upload a financial document (PDF only). Requires 'upload' permission."""
    doc = await document_service.upload_document(
        file, title, company_name, document_type, current_user, db
    )
    return _to_out(doc)


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("view")),
):
    """Retrieve all documents."""
    return [_to_out(d) for d in document_service.get_all_documents(db)]


@router.get("/search", response_model=list[DocumentOut])
def search_documents(
    title: str | None = Query(None),
    company_name: str | None = Query(None),
    document_type: DocumentType | None = Query(None),
    uploaded_by: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("view")),
):
    """Search documents by metadata fields."""
    docs = document_service.search_documents(db, title, company_name, document_type, uploaded_by)
    return [_to_out(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("view")),
):
    """Retrieve details of a specific document."""
    return _to_out(document_service.get_document_by_id(document_id, db))


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a document. Only the owner or admin can delete."""
    return document_service.delete_document(document_id, current_user, db)
