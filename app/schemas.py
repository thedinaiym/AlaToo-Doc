from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import DocumentStatus, UserRole


class UserCreate(BaseModel):
    university_id: str
    full_name: str
    role: UserRole
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    university_id: str
    full_name: str
    faculty: str | None = None
    role: UserRole


class BroadcastRequest(BaseModel):
    title: str
    text: str
    target_faculty: str


class BroadcastResponse(BaseModel):
    created_count: int
    target_faculty: str


class LoginRequest(BaseModel):
    university_id: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class DocumentCreate(BaseModel):
    title: str
    raw_text: str
    file_url: str | None = None
    recipient_id: uuid.UUID


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    doc_type: str | None = None
    raw_text: str
    file_url: str | None
    status: DocumentStatus
    creator_id: uuid.UUID
    recipient_id: uuid.UUID


class SignatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    user_id: uuid.UUID
    signature_hash: str
    signed_at: datetime


class DocumentDetailResponse(DocumentResponse):
    signatures: list[SignatureResponse] = []
