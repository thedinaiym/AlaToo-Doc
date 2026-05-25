import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    dean = "dean"
    admin = "admin"


class DocumentStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    signed = "signed"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    university_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255))

    created_documents: Mapped[list["Document"]] = relationship(
        back_populates="creator",
        foreign_keys="Document.creator_id",
    )
    received_documents: Mapped[list["Document"]] = relationship(
        back_populates="recipient",
        foreign_keys="Document.recipient_id",
    )
    signatures: Mapped[list["Signature"]] = relationship(back_populates="user")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text)
    file_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.draft,
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    creator: Mapped[User] = relationship(
        back_populates="created_documents",
        foreign_keys=[creator_id],
    )
    recipient: Mapped[User] = relationship(
        back_populates="received_documents",
        foreign_keys=[recipient_id],
    )
    signatures: Mapped[list["Signature"]] = relationship(back_populates="document")


class Signature(Base):
    __tablename__ = "signatures"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    signature_hash: Mapped[str] = mapped_column(String(255))
    signed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped[Document] = relationship(back_populates="signatures")
    user: Mapped[User] = relationship(back_populates="signatures")
