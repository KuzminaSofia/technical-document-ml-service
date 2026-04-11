from __future__ import annotations

from sqlalchemy.orm import Session

from technical_document_ml_service.core.security import hash_password, verify_password
from technical_document_ml_service.domain.entities import User
from technical_document_ml_service.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
)
from technical_document_ml_service.services.user_service import (
    create_user,
    get_user_by_email,
)


def register_user(
    session: Session,
    *,
    email: str,
    password: str,
) -> User:
    """зарегистрировать нового пользователя"""
    normalized_email = email.strip().lower()
    password_hash = hash_password(password)

    return create_user(
        session,
        email=normalized_email,
        password_hash=password_hash,
    )


def authenticate_user(
    session: Session,
    *,
    email: str,
    password: str,
) -> User:
    """аутентифицировать пользователя по email и паролю"""
    normalized_email = email.strip().lower()
    user = get_user_by_email(session, normalized_email)

    if user is None:
        raise AuthenticationError("Неверный email или пароль.")

    if not user.check_password(password, verify_password):
        raise AuthenticationError("Неверный email или пароль.")

    if not user.is_active:
        raise AuthorizationError("Пользователь деактивирован.")

    return user