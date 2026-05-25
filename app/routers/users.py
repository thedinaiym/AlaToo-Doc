from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import get_current_user
from app.models import User, UserRole
from app.schemas import UserResponse


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def get_users(
    role: UserRole | None = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[UserResponse]:
    query = select(User)
    if role is not None:
        query = query.where(User.role == role)

    result = await session.execute(query.order_by(User.full_name))
    return list(result.scalars().all())
