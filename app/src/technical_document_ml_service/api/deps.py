from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from technical_document_ml_service.db.session import get_db_session, get_read_session
from technical_document_ml_service.domain.entities import User
from technical_document_ml_service.domain.exceptions import AuthenticationError
from technical_document_ml_service.services.auth_service import authenticate_user


http_basic = HTTPBasic(auto_error=False)

SessionDep = Annotated[Session, Depends(get_db_session)]
ReadSessionDep = Annotated[Session, Depends(get_read_session)]


def _authenticate_from_credentials(
    credentials: HTTPBasicCredentials | None,
    session: Session,
) -> User:
    """выполнить аутентификацию пользователя по Basic Auth"""
    if credentials is None:
        raise AuthenticationError("Не переданы учетные данные.")

    return authenticate_user(
        session,
        email=credentials.username,
        password=credentials.password,
    )


def get_current_user(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(http_basic)],
    session: SessionDep,
) -> User:
    """получить текущего пользователя через write-session"""
    return _authenticate_from_credentials(credentials, session)


def get_current_read_user(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(http_basic)],
    session: ReadSessionDep,
) -> User:
    """получить текущего пользователя через read-session"""
    return _authenticate_from_credentials(credentials, session)


CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentReadUserDep = Annotated[User, Depends(get_current_read_user)]