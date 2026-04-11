from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from technical_document_ml_service.db.session import get_db_session
from technical_document_ml_service.domain.entities import User
from technical_document_ml_service.domain.exceptions import AuthenticationError
from technical_document_ml_service.services.auth_service import authenticate_user


http_basic = HTTPBasic(auto_error=False)

SessionDep = Annotated[Session, Depends(get_db_session)]


def get_current_user(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(http_basic)],
    session: SessionDep,
) -> User:
    """получить текущего пользователя из Basic Auth"""
    if credentials is None:
        raise AuthenticationError("Не переданы учетные данные.")

    return authenticate_user(
        session,
        email=credentials.username,
        password=credentials.password,
    )


CurrentUserDep = Annotated[User, Depends(get_current_user)]