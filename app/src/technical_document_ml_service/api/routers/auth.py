from __future__ import annotations

from fastapi import APIRouter, status

from technical_document_ml_service.api.deps import SessionDep
from technical_document_ml_service.api.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
)
from technical_document_ml_service.api.schemas.users import UserResponse
from technical_document_ml_service.services.auth_service import (
    authenticate_user,
    register_user,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest, session: SessionDep) -> AuthResponse:
    with session.begin():
        user = register_user(
            session,
            email=payload.email,
            password=payload.password,
        )

    return AuthResponse(
        message="Пользователь успешно зарегистрирован.",
        user=UserResponse.from_domain(user),
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, session: SessionDep) -> AuthResponse:
    user = authenticate_user(
        session,
        email=payload.email,
        password=payload.password,
    )

    return AuthResponse(
        message="Аутентификация прошла успешно.",
        user=UserResponse.from_domain(user),
    )