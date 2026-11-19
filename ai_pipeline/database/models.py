"""SQLAlchemy models for documents, pages, fields, audit history and API keys."""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .connection import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(32), primary_key=True)
    filename = Column(String(512), nullable=False)
    stored_path = Column(String(1024), nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    size_bytes = Column(Integer, nullable=False, default=0)
    mime_type = Column(String(128))
    document_type = Column(String(64), nullable=False, default="unknown")
    declared_document_type = Column(String(64))
    state = Column(String(64), nullable=False, default="telangana")
    district = Column(String(128))
    language = Column(String(32))
    status = Column(String(32), nullable=False, default="uploaded", index=True)
    total_pages = Column(Integer, nullable=False, default=0)
    overall_confidence = Column(Float)
    extraction_method = Column(String(32), nullable=False, default="none")
    summary = Column(JSON, nullable=False, default=dict)
    validation = Column(JSON, nullable=False, default=dict)
    warnings = Column(JSON, nullable=False, default=list)
    stages = Column(JSON, nullable=False, default=list)
    created_at = Column(String(32), nullable=False)
    updated_at = Column(String(32), nullable=False)

    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    fields = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(32), ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_number = Column(Integer, nullable=False)
    image_path = Column(String(1024), nullable=False)
    width = Column(Integer, nullable=False, default=0)
    height = Column(Integer, nullable=False, default=0)
    quality = Column(JSON, nullable=False, default=dict)
    ocr_lines = Column(JSON, nullable=False, default=list)

    document = relationship("Document", back_populates="pages")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(32), ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    field_name = Column(String(64), nullable=False, index=True)
    value = Column(Text)
    payload = Column(JSON, nullable=False, default=dict)

    document = relationship("Document", back_populates="fields")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(32), nullable=False, index=True)
    timestamp = Column(String(32), nullable=False)
    user = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False)
    action = Column(String(32), nullable=False)
    field_changed = Column(String(64))
    old_value = Column(Text)
    new_value = Column(Text)
    details = Column(Text)
    ip_address = Column(String(64))


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(32), primary_key=True)
    name = Column(String(128), nullable=False)
    prefix = Column(String(32), nullable=False)
    role = Column(String(32), nullable=False)
    created = Column(String(32), nullable=False)
    last_used = Column(String(32))
    revoked = Column(Boolean, nullable=False, default=False)
