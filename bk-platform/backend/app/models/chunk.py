from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    content: Mapped[str]
    embedding: Mapped[bytes | None] = mapped_column(nullable=True)  # optional persist
    position: Mapped[int] = mapped_column(Integer, default=0)

    document = relationship("Document", back_populates="chunks")
