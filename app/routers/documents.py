import uuid
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from groq import AsyncGroq, GroqError
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session, get_settings
from app.dependencies import get_current_user
from app.models import Document, DocumentStatus, Signature, User, UserRole
from app.pdf_engine import DocumentType, render_document_to_pdf
from app.schemas import (
    DocumentCreate,
    DocumentDetailResponse,
    DocumentLanguage,
    DocumentResponse,
    StudentSex,
)


LANGUAGE_CONTENT = {
    DocumentLanguage.english: {
        "name": "English",
        "system_prompt": (
            "You are a professional digital university document clerk for Alatoo. "
            "Write a strict official application in English based on the user's data. "
            "Return ONLY the finished application text, with no extra phrases or comments."
        ),
        "student_name": "Student full name",
        "faculty": "Faculty",
        "recipient": "Addressed to",
        "sex": "Student sex",
        "sex_values": {
            StudentSex.male: "male",
            StudentSex.female: "female",
        },
        "reason": "Reason for application",
        "application_title": "APPLICATION",
        "missing_faculty": "Not specified",
        "missing_group": "Not specified",
        "recipient_titles": {
            UserRole.dean: "To the Dean",
            UserRole.teacher: "To the Teacher",
            UserRole.admin: "To the Administrator",
            UserRole.student: "To the Student",
        },
        "default_recipient_title": "To the Recipient",
        "from_student_label": "from student",
        "group_label": "Group",
        "registration_label": "Registration No.",
        "signed_label": "SIGNED ELECTRONICALLY",
    },
    DocumentLanguage.russian: {
        "name": "Russian",
        "system_prompt": (
            "Ты — профессиональный цифровой делопроизводитель университета Alatoo. "
            "Составь строгое официальное заявление на русском языке на основе данных пользователя. "
            "Верни ТОЛЬКО готовый текст заявления, без лишних фраз и комментариев."
        ),
        "student_name": "ФИО студента",
        "faculty": "Факультет",
        "recipient": "Кому адресовано",
        "sex": "Пол студента",
        "sex_values": {
            StudentSex.male: "мужской",
            StudentSex.female: "женский",
        },
        "reason": "Причина обращения",
        "application_title": "ЗАЯВЛЕНИЕ",
        "missing_faculty": "Не указан",
        "missing_group": "Не указана",
        "recipient_titles": {
            UserRole.dean: "Декану",
            UserRole.teacher: "Преподавателю",
            UserRole.admin: "Администратору",
            UserRole.student: "Студенту",
        },
        "default_recipient_title": "Получателю",
        "from_student_label": "от студента",
        "group_label": "Группа",
        "registration_label": "Регистрационный №",
        "signed_label": "ПОДПИСАНО ЭП",
    },
    DocumentLanguage.kyrgyz: {
        "name": "Kyrgyz",
        "system_prompt": (
            "Сен Alatoo университетинин кесипкөй санарип иш кагаздарын жүргүзүүчүсүсүң. "
            "Колдонуучунун маалыматтарынын негизинде кыргыз тилинде расмий арыз түз. "
            "Даяр арыздын текстин гана кайтар, кошумча түшүндүрмө же комментарий жазба."
        ),
        "student_name": "Студенттин аты-жөнү",
        "faculty": "Факультет",
        "recipient": "Кимге",
        "sex": "Студенттин жынысы",
        "sex_values": {
            StudentSex.male: "эркек",
            StudentSex.female: "аял",
        },
        "reason": "Кайрылуунун себеби",
        "application_title": "АРЫЗ",
        "missing_faculty": "Көрсөтүлгөн эмес",
        "missing_group": "Көрсөтүлгөн эмес",
        "recipient_titles": {
            UserRole.dean: "Деканга",
            UserRole.teacher: "Окутуучуга",
            UserRole.admin: "Администраторго",
            UserRole.student: "Студентке",
        },
        "default_recipient_title": "Алуучуга",
        "from_student_label": "студенттен",
        "group_label": "Тайпа",
        "registration_label": "Каттоо №",
        "signed_label": "ЭЛЕКТРОНДУК КОЛ ТАМГА КОЮЛДУ",
    },
}

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
GENERATED_PDF_DIR = Path("static") / "generated_pdfs"


def get_language_content(language: DocumentLanguage) -> dict:
    return LANGUAGE_CONTENT.get(language, LANGUAGE_CONTENT[DocumentLanguage.russian])


def get_recipient_title(role: UserRole, language: DocumentLanguage) -> str:
    content = get_language_content(language)
    return content["recipient_titles"].get(role, content["default_recipient_title"])


def build_pdf_context(
    *,
    title: str,
    document_id: uuid.UUID,
    current_user: User,
    recipient: User,
    final_text: str,
    language: DocumentLanguage,
) -> dict:
    content = get_language_content(language)
    return {
        "title": title,
        "application_title": content["application_title"],
        "doc_number": f"{datetime.now().year}-{str(document_id)[:8].upper()}",
        "student_name": current_user.full_name,
        "student_id": current_user.university_id,
        "faculty": current_user.faculty or content["missing_faculty"],
        "group_or_faculty": current_user.faculty or content["missing_group"],
        "recipient_title": get_recipient_title(recipient.role, language),
        "recipient_name": recipient.full_name,
        "date": datetime.now().strftime("%d.%m.%Y"),
        "final_text": final_text,
        "logo_path": "frontend/public/logo.png",
        "from_student_label": content["from_student_label"],
        "group_label": content["group_label"],
        "registration_label": content["registration_label"],
        "signed_label": content["signed_label"],
    }


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
            "doc_type": document.doc_type,
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
        doc_type=DocumentType.student_complaint.value,
        raw_text=payload.raw_text,
        status=DocumentStatus.pending,
        creator_id=current_user.id,
        recipient_id=payload.recipient_id,
    )
    session.add(document)
    await session.flush()

    pdf_filename = f"{document.id}.pdf"
    pdf_path = Path("static") / "pdfs" / pdf_filename
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(
        render_document_to_pdf(
            DocumentType.student_complaint.value,
            build_pdf_context(
                title=document.title,
                document_id=document.id,
                current_user=current_user,
                recipient=recipient,
                final_text=document.raw_text,
                language=payload.language,
            ),
        )
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


class FinalizeDocumentRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    doc_type: DocumentType
    recipient_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=255)
    final_text: str = Field(..., min_length=1)
    language: DocumentLanguage = DocumentLanguage.russian


class FinalizeDocumentResponse(DocumentResponse):
    download_url: str


@router.post(
    "/finalize",
    response_model=FinalizeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def finalize_document(
    payload: FinalizeDocumentRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> FinalizeDocumentResponse:
    requested_student_id = payload.student_id.strip()
    current_student_ids = {str(current_user.id), current_user.university_id}

    if requested_student_id not in current_student_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can finalize documents only for your own student account",
        )

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
        doc_type=payload.doc_type.value,
        raw_text=payload.final_text,
        status=DocumentStatus.pending,
        creator_id=current_user.id,
        recipient_id=recipient.id,
    )
    session.add(document)
    await session.flush()

    pdf_bytes = render_document_to_pdf(
        payload.doc_type.value,
        build_pdf_context(
            title=payload.title,
            document_id=document.id,
            current_user=current_user,
            recipient=recipient,
            final_text=payload.final_text,
            language=payload.language,
        ),
    )

    GENERATED_PDF_DIR.mkdir(parents=True, exist_ok=True)
    pdf_filename = f"{document.id}.pdf"
    pdf_path = GENERATED_PDF_DIR / pdf_filename
    pdf_path.write_bytes(pdf_bytes)
    document.file_url = f"/static/generated_pdfs/{pdf_filename}"

    await session.commit()
    await session.refresh(document)

    return FinalizeDocumentResponse.model_validate(
        {
            "id": document.id,
            "title": document.title,
            "doc_type": document.doc_type,
            "raw_text": document.raw_text,
            "file_url": document.file_url,
            "status": document.status,
            "creator_id": document.creator_id,
            "recipient_id": document.recipient_id,
            "download_url": document.file_url,
        }
    )


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
    sex: StudentSex
    reason: str = Field(..., min_length=1)
    language: DocumentLanguage = DocumentLanguage.russian


class DocumentPredictionResponse(BaseModel):
    generated_text: str


@lru_cache
def get_groq_client() -> AsyncGroq:
    api_key = get_settings().groq_api_key

    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set")

    return AsyncGroq(api_key=api_key)


def build_user_prompt(payload: DocumentPredictionRequest) -> str:
    content = get_language_content(payload.language)
    return (
        f"{content['student_name']}: {payload.student_name}\n"
        f"{content['faculty']}: {payload.faculty}\n"
        f"{content['recipient']}: {payload.recipient_title}\n"
        f"{content['sex']}: {content['sex_values'][payload.sex]}\n"
        f"{content['reason']}: {payload.reason}"
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
            model=get_settings().groq_model,
            messages=[
                {
                    "role": "system",
                    "content": get_language_content(payload.language)["system_prompt"],
                },
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
