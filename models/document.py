from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, index=True)
    company_name = Column(String, nullable=False, index=True)
    document_type = Column(String, nullable=False)   # invoice | report | contract
    file_path = Column(String, nullable=False)        # path on disk
    file_name = Column(String, nullable=False)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_indexed = Column(Boolean, default=False)       # True once embeddings are stored

    uploader = relationship("User", back_populates="documents")
