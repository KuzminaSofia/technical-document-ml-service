from __future__ import annotations

from fastapi import APIRouter

from technical_document_ml_service.api.deps import CurrentReadUserDep
from technical_document_ml_service.api.schemas.users import UserResponse


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentReadUserDep) -> UserResponse:
    """получить данные текущего пользователя"""
    return UserResponse.from_domain(current_user)