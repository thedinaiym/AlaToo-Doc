import os
import uuid
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from groq import AsyncGroq, GroqError
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import get_current_user
from app.models import Document, DocumentStatus, Signature, User, UserRole
from app.schemas import DocumentCreate, DocumentDetailResponse, DocumentResponse
from app.services.pdf_service import generate_document_pdf


SYSTEM_PROMPT = (
    "Ты — профессиональный цифровой делопроизводитель университета Alatoo. "
    "Составь строгое официальное заявление на основе данных пользователя. "
    "Верни ТОЛЬКО готовый текст заявления, без лишних фраз и комментариев."
)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


async def get_document_for_user(
    document_id: uuid.UUID,
    current_user: User,
    session: AsyncSession,
) -> Document:
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if (
        document.creator_id != current_user.id
        and document.recipient_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this document",
        )

    return document


async def build_document_detail(
    document: Document,
    session: AsyncSession,
) -> DocumentDetailResponse:
    result = await session.execute(
        select(Signature).where(Signature.document_id == document.id)
    )
    signatures = list(result.scalars().all())
    return DocumentDetailResponse.model_validate(
        {
            "id": document.id,
            "title": document.title,
            "raw_text": document.raw_text,
            "file_url": document.file_url,
            "status": document.status,
            "creator_id": document.creator_id,
            "recipient_id": document.recipient_id,
            "signatures": signatures,
        }
    )


@router.post(
    "/create",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    payload: DocumentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentResponse:
    recipient_result = await session.execute(
        select(User).where(User.id == payload.recipient_id)
    )
    recipient = recipient_result.scalar_one_or_none()
    if recipient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found",
        )

    document = Document(
        title=payload.title,
        raw_text=payload.raw_text,
        status=DocumentStatus.pending,
        creator_id=current_user.id,
        recipient_id=payload.recipient_id,
    )
    session.add(document)
    await session.flush()

    pdf_filename = f"{document.id}.pdf"
    pdf_path = Path("static") / "pdfs" / pdf_filename
    generate_document_pdf(
        title=document.title,
        text=document.raw_text,
        output_path=str(pdf_path),
    )
    document.file_url = f"/static/pdfs/{pdf_filename}"

    await session.commit()
    await session.refresh(document)

    return document


@router.get("/outbox", response_model=list[DocumentResponse])
async def get_outbox_documents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[DocumentResponse]:
    result = await session.execute(
        select(Document).where(Document.creator_id == current_user.id)
    )
    return list(result.scalars().all())


@router.get("/inbox", response_model=list[DocumentResponse])
async def get_inbox_documents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[DocumentResponse]:
    result = await session.execute(
        select(Document).where(
            Document.recipient_id == current_user.id,
            Document.status == DocumentStatus.pending,
        )
    )
    return list(result.scalars().all())


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentDetailResponse:
    document = await get_document_for_user(document_id, current_user, session)
    return await build_document_detail(document, session)


@router.post("/{document_id}/sign", response_model=DocumentDetailResponse)
async def sign_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentDetailResponse:
    document = await get_document_for_user(document_id, current_user, session)

    if current_user.role != UserRole.dean or document.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the recipient dean can sign this document",
        )

    if document.status != DocumentStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending documents can be signed",
        )

    signature = Signature(
        document_id=document.id,
        user_id=current_user.id,
        signature_hash=f"signed:{document.id}:{current_user.id}",
    )
    document.status = DocumentStatus.signed
    session.add(signature)
    await session.commit()
    await session.refresh(document)

    return await build_document_detail(document, session)


@router.post("/{document_id}/reject", response_model=DocumentDetailResponse)
async def reject_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentDetailResponse:
    document = await get_document_for_user(document_id, current_user, session)

    if current_user.role != UserRole.dean or document.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the recipient dean can reject this document",
        )

    if document.status != DocumentStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending documents can be rejected",
        )

    document.status = DocumentStatus.rejected
    await session.commit()
    await session.refresh(document)

    return await build_document_detail(document, session)


class DocumentPredictionRequest(BaseModel):
    student_name: str = Field(..., min_length=1)
    faculty: str = Field(..., min_length=1)
    recipient_title: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class DocumentPredictionResponse(BaseModel):
    generated_text: str


@lru_cache
def get_groq_client() -> AsyncGroq:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set")

    return AsyncGroq(api_key=api_key)


def build_user_prompt(payload: DocumentPredictionRequest) -> str:
    return (
        f"ФИО студента: {payload.student_name}\n"
        f"Факультет: {payload.faculty}\n"
        f"Кому адресовано: {payload.recipient_title}\n"
        f"Причина обращения: {payload.reason}"
    )


@router.post("/predict-text", response_model=DocumentPredictionResponse)
async def predict_document_text(
    payload: DocumentPredictionRequest,
) -> DocumentPredictionResponse:
    try:
        client = get_groq_client()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    try:
        completion = await client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(payload)},
            ],
            temperature=0.2,
        )
    except GroqError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI text generation service is unavailable",
        ) from exc

    generated_text = completion.choices[0].message.content

    if not generated_text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI text generation returned an empty response",
        )

    return DocumentPredictionResponse(generated_text=generated_text.strip())
