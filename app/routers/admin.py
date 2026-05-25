from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import get_current_user
from app.models import Document, DocumentStatus, User, UserRole
from app.schemas import BroadcastRequest, BroadcastResponse
from app.services.pdf_service import generate_document_pdf


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/broadcast", response_model=BroadcastResponse)
async def broadcast_document(
    payload: BroadcastRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> BroadcastResponse:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can broadcast documents",
        )

    result = await session.execute(
        select(User).where(
            User.role == UserRole.student,
            User.faculty == payload.target_faculty,
        )
    )
    students = list(result.scalars().all())

    documents = [
        Document(
            title=payload.title,
            raw_text=payload.text,
            status=DocumentStatus.pending,
            creator_id=current_user.id,
            recipient_id=student.id,
        )
        for student in students
    ]

    if not documents:
        return BroadcastResponse(
            created_count=0,
            target_faculty=payload.target_faculty,
        )

    session.add_all(documents)
    await session.flush()

    for document in documents:
        pdf_filename = f"{document.id}.pdf"
        pdf_path = Path("static") / "pdfs" / pdf_filename
        generate_document_pdf(
            title=document.title,
            text=document.raw_text,
            output_path=str(pdf_path),
        )
        document.file_url = f"/static/pdfs/{pdf_filename}"

    await session.commit()

    return BroadcastResponse(
        created_count=len(documents),
        target_faculty=payload.target_faculty,
    )
