from __future__ import annotations

from fastapi import APIRouter

from technical_document_ml_service.api.deps import CurrentUserDep
from technical_document_ml_service.api.schemas.users import UserResponse


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUserDep) -> UserResponse:
    return UserResponse.from_domain(current_user)