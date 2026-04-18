from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Response, status

from technical_document_ml_service.api.deps import ReadSessionDep, SessionDep
from technical_document_ml_service.api.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    TokenResponse,
)
from technical_document_ml_service.api.schemas.users import UserResponse
from technical_document_ml_service.core.security import (
    create_access_token,
    get_auth_cookie_name,
    get_jwt_expire_minutes,
    is_auth_cookie_secure,
)
from technical_document_ml_service.services.auth_service import (
    authenticate_user,
    register_user,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def _build_access_token(user_id: UUID, email: str) -> tuple[str, int]:
    """создать access token и вернуть его вместе со сроком жизни в секундах"""
    expires_delta = timedelta(minutes=get_jwt_expire_minutes())
    expires_in_seconds = int(expires_delta.total_seconds())

    access_token = create_access_token(
        user_id=user_id,
        email=email,
        expires_delta=expires_delta,
    )
    return access_token, expires_in_seconds


def _set_auth_cookie(
    response: Response,
    access_token: str,
    expires_in_seconds: int,
) -> None:
    """установить HttpOnly cookie с JWT access token"""
    response.set_cookie(
        key=get_auth_cookie_name(),
        value=access_token,
        max_age=expires_in_seconds,
        expires=expires_in_seconds,
        path="/",
        httponly=True,
        samesite="lax",
        secure=is_auth_cookie_secure(),
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest, session: SessionDep) -> AuthResponse:
    """зарегистрировать нового пользователя"""
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
def login(
    payload: LoginRequest,
    response: Response,
    session: ReadSessionDep,
) -> AuthResponse:
    """
    аутентифицировать пользователя по email и паролю

    Для удобства Web UI endpoint также устанавливает JWT cookie.
    При этом контракт ответа остается прежним.
    """
    user = authenticate_user(
        session,
        email=payload.email,
        password=payload.password,
    )

    access_token, expires_in_seconds = _build_access_token(
        user_id=user.id,
        email=user.email,
    )
    _set_auth_cookie(response, access_token, expires_in_seconds)

    return AuthResponse(
        message="Аутентификация прошла успешно.",
        user=UserResponse.from_domain(user),
    )


@router.post("/token", response_model=TokenResponse)
def issue_access_token(
    payload: LoginRequest,
    response: Response,
    session: ReadSessionDep,
) -> TokenResponse:
    """
    аутентифицировать пользователя и выдать JWT access token

    endpoint полезен для клиентов, которым нужен токен в теле ответа.
    Также устанавливает auth-cookie.
    """
    user = authenticate_user(
        session,
        email=payload.email,
        password=payload.password,
    )

    access_token, expires_in_seconds = _build_access_token(
        user_id=user.id,
        email=user.email,
    )
    _set_auth_cookie(response, access_token, expires_in_seconds)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_seconds=expires_in_seconds,
        user=UserResponse.from_domain(user),
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(response: Response) -> LogoutResponse:
    """
    очистить JWT cookie текущего пользователя

    Endpoint намеренно не требует обязательной авторизации:
    logout должен быть идемпотентным и успешно очищать cookie,
    даже если пользователь уже разлогинен или токен истек.
    """
    response.delete_cookie(
        key=get_auth_cookie_name(),
        path="/",
        httponly=True,
        samesite="lax",
        secure=is_auth_cookie_secure(),
    )

    return LogoutResponse(message="Вы успешно вышли из системы.")