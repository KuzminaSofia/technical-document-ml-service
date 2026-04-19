from __future__ import annotations

from urllib.parse import urlparse

from fastapi import HTTPException, Request, status


def ensure_same_origin(request: Request) -> None:
    """
    минимальная CSRF-защита для server-rendered форм
    """
    expected_host = request.headers.get("host") or request.url.netloc

    origin = request.headers.get("origin")
    if origin:
        parsed_origin = urlparse(origin)
        if parsed_origin.netloc == expected_host:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF verification failed.",
        )

    referer = request.headers.get("referer")
    if referer:
        parsed_referer = urlparse(referer)
        if parsed_referer.netloc == expected_host:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF verification failed.",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="CSRF verification failed.",
    )