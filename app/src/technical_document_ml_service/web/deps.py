from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBasicCredentials

from technical_document_ml_service.api.deps import (
    ReadSessionDep,
    authenticate_request,
    http_basic,
    http_bearer,
)
from technical_document_ml_service.domain.entities import User
from technical_document_ml_service.domain.exceptions import AuthenticationError


def get_optional_web_user(
    request: Request,
    session: ReadSessionDep,
    basic_credentials: Annotated[HTTPBasicCredentials | None, Depends(http_basic)],
    bearer_credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(http_bearer),
    ],
) -> User | None:
    """
    получить текущего пользователя для web-страниц
    """
    try:
        return authenticate_request(
            request=request,
            session=session,
            basic_credentials=basic_credentials,
            bearer_credentials=bearer_credentials,
        )
    except AuthenticationError:
        return None


CurrentOptionalWebUserDep = Annotated[User | None, Depends(get_optional_web_user)]