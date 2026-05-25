import os
from functools import lru_cache

from fastapi import APIRouter, HTTPException, status
from groq import AsyncGroq, GroqError
from pydantic import BaseModel, Field


SYSTEM_PROMPT = (
    "Ты — профессиональный цифровой делопроизводитель университета Alatoo. "
    "Составь строгое официальное заявление на основе данных пользователя. "
    "Верни ТОЛЬКО готовый текст заявления, без лишних фраз и комментариев."
)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


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
