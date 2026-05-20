import os
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from models.document import Document
from models.user import User
from config import get_settings

settings = get_settings()
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"invoice", "report", "contract"}


async def upload_document(
    file: UploadFile,
    title: str,
    company_name: str,
    document_type: str,
    current_user: User,
    db: Session,
) -> Document:
    if document_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"document_type must be one of {ALLOWED_TYPES}")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Save file to disk
    dest_dir = UPLOAD_DIR / current_user.id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file.filename

    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(
        title=title,
        company_name=company_name,
        document_type=document_type,
        file_path=str(dest_path),
        file_name=file.filename,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_all_documents(db: Session) -> list[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()


def get_document_by_id(document_id: str, db: Session) -> Document:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def delete_document(document_id: str, current_user: User, db: Session) -> dict:
    doc = get_document_by_id(document_id, db)

    # Only admin or the uploader can delete
    is_admin = current_user.has_permission("all")
    is_owner = doc.uploaded_by == current_user.id
    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Not authorised to delete this document")

    # Remove file from disk
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    return {"message": f"Document '{doc.title}' deleted successfully"}


def search_documents(
    db: Session,
    title: str | None = None,
    company_name: str | None = None,
    document_type: str | None = None,
    uploaded_by: str | None = None,
) -> list[Document]:
    q = db.query(Document)
    if title:
        q = q.filter(Document.title.ilike(f"%{title}%"))
    if company_name:
        q = q.filter(Document.company_name.ilike(f"%{company_name}%"))
    if document_type:
        q = q.filter(Document.document_type == document_type)
    if uploaded_by:
        q = q.filter(Document.uploaded_by == uploaded_by)
    return q.order_by(Document.created_at.desc()).all()
