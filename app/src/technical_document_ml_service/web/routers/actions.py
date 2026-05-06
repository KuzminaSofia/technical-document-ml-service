from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID

from fastapi import APIRouter, Form, Request, UploadFile
from fastapi.responses import RedirectResponse, Response

from technical_document_ml_service.api.deps import ReadSessionDep, SessionDep
from technical_document_ml_service.core.security import (
    create_access_token,
    get_auth_cookie_name,
    get_jwt_expire_minutes,
    is_auth_cookie_secure,
)
from technical_document_ml_service.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
)
from technical_document_ml_service.services.auth_service import (
    authenticate_user,
    register_user,
)
from technical_document_ml_service.services.billing_service import credit_balance
from technical_document_ml_service.services.document_storage_service import (
    IncomingDocumentData,
)
from technical_document_ml_service.services.prediction_submission_service import (
    submit_document_prediction,
)
from technical_document_ml_service.web.deps import CurrentOptionalWebUserDep
from technical_document_ml_service.web.model_catalog import get_active_models
from technical_document_ml_service.web.security import ensure_same_origin
from technical_document_ml_service.web.templating import render_template


logger = logging.getLogger(__name__)
router = APIRouter(tags=["web-actions"])


def _forge_page_context(active_page: str | None = None) -> dict:
    """общий layout-контекст для авторизованных страниц с левым sidebar"""
    return {
        "body_class": "body-full-width",
        "page_content_class": "page-content-full-width",
        "hide_site_header": True,
        "active_page": active_page,
    }


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


@router.post("/login", name="login_action")
def login_action(
    request: Request,
    session: ReadSessionDep,
    email: str = Form(...),
    password: str = Form(...),
):
    """обработать web-форму входа"""
    ensure_same_origin(request)
    normalized_email = email.strip().lower()

    try:
        user = authenticate_user(
            session,
            email=normalized_email,
            password=password,
        )
    except (AuthenticationError, AuthorizationError) as exc:
        return render_template(
            request,
            "login.html",
            page_title="Вход",
            current_user=None,
            form_data={"email": normalized_email},
            error_message=str(exc),
            status_code=401,
        )
    except Exception:
        logger.exception("Unexpected error during web login.")
        return render_template(
            request,
            "login.html",
            page_title="Вход",
            current_user=None,
            form_data={"email": normalized_email},
            error_message="Не удалось выполнить вход. Попробуйте ещё раз.",
            status_code=500,
        )

    access_token, expires_in_seconds = _build_access_token(
        user_id=user.id,
        email=user.email,
    )

    response = RedirectResponse(url="/dashboard", status_code=303)
    _set_auth_cookie(response, access_token, expires_in_seconds)
    return response


@router.post("/register", name="register_action")
def register_action(
    request: Request,
    session: SessionDep,
    email: str = Form(...),
    password: str = Form(...),
):
    """обработать web-форму регистрации"""
    ensure_same_origin(request)
    normalized_email = email.strip().lower()

    try:
        user = register_user(
            session,
            email=normalized_email,
            password=password,
        )
    except Exception:
        logger.exception("Unexpected error during web registration.")
        return render_template(
            request,
            "register.html",
            page_title="Регистрация",
            current_user=None,
            form_data={"email": normalized_email},
            error_message=(
                "Не удалось зарегистрировать пользователя. "
                "Проверьте корректность данных или попробуйте другой email."
            ),
            status_code=400,
        )

    access_token, expires_in_seconds = _build_access_token(
        user_id=user.id,
        email=user.email,
    )

    response = RedirectResponse(url="/dashboard", status_code=303)
    _set_auth_cookie(response, access_token, expires_in_seconds)
    return response


@router.post("/logout", name="logout_action")
def logout_action(request: Request):
    """выйти из web-интерфейса"""
    ensure_same_origin(request)

    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(
        key=get_auth_cookie_name(),
        path="/",
        httponly=True,
        samesite="lax",
        secure=is_auth_cookie_secure(),
    )
    return response


@router.post("/balance-ui/top-up", name="top_up_action")
def top_up_action(
    request: Request,
    session: SessionDep,
    current_user: CurrentOptionalWebUserDep,
    amount: str = Form(...),
):
    """обработать форму пополнения баланса"""
    ensure_same_origin(request)

    if current_user is None:
        return RedirectResponse(url="/login", status_code=303)

    try:
        parsed_amount = Decimal(amount)
        if parsed_amount <= Decimal("0"):
            raise ValueError
    except (InvalidOperation, ValueError):
        return render_template(
            request,
            "balance.html",
            page_title="Баланс",
            current_user=current_user,
            success_message=None,
            error_message="Введите корректную положительную сумму пополнения.",
            form_data={"amount": amount},
            status_code=400,
            **_forge_page_context(None),
        )

    try:
        credit_balance(
            session,
            user_id=current_user.id,
            amount=parsed_amount,
        )
    except Exception:
        logger.exception("Unexpected error during balance top-up.")
        return render_template(
            request,
            "balance.html",
            page_title="Баланс",
            current_user=current_user,
            success_message=None,
            error_message="Не удалось пополнить баланс. Попробуйте ещё раз.",
            form_data={"amount": amount},
            status_code=500,
            **_forge_page_context(None),
        )

    return RedirectResponse(url="/balance-ui?success=topup", status_code=303)


@router.post("/predict-ui", name="predict_submit_action")
def predict_submit_action(
    request: Request,
    session: SessionDep,
    current_user: CurrentOptionalWebUserDep,
    model_name: str = Form(...),
    target_schema: str = Form(...),
    documents: list[UploadFile] | None = None,
):
    """обработать web-форму отправки ML-задачи"""
    ensure_same_origin(request)

    if current_user is None:
        return RedirectResponse(url="/login", status_code=303)

    models = get_active_models(session)

    if not documents:
        return render_template(
            request,
            "predict.html",
            page_title="Новая обработка",
            current_user=current_user,
            models=models,
            error_message="Нужно загрузить хотя бы один документ.",
            form_data={
                "model_name": model_name,
                "target_schema": target_schema,
            },
            status_code=400,
            **_forge_page_context("predict"),
        )

    incoming_documents: list[IncomingDocumentData] = []

    try:
        for document in documents:
            content = document.file.read()
            incoming_documents.append(
                IncomingDocumentData(
                    filename=document.filename or "document",
                    content_type=document.content_type,
                    content=content,
                )
            )
    finally:
        for document in documents:
            document.file.close()

    try:
        submission = submit_document_prediction(
            session,
            user_id=current_user.id,
            model_name=model_name,
            target_schema=target_schema,
            documents=incoming_documents,
        )
    except Exception:
        logger.exception("Unexpected error during web prediction submission.")
        return render_template(
            request,
            "predict.html",
            page_title="Новая обработка",
            current_user=current_user,
            models=models,
            error_message=(
                "Не удалось отправить задачу. "
                "Проверьте баланс, выбранную модель и загруженные документы."
            ),
            form_data={
                "model_name": model_name,
                "target_schema": target_schema,
            },
            status_code=400,
            **_forge_page_context("predict"),
        )

    return RedirectResponse(
        url=f"/tasks-ui/{submission.task_id}",
        status_code=303,
    )