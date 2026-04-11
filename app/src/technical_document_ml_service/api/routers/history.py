from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from technical_document_ml_service.api.deps import CurrentUserDep, SessionDep
from technical_document_ml_service.api.schemas.history import (
    PaginationParams,
    PredictionHistoryItemResponse,
    PredictionsHistoryResponse,
    TransactionHistoryItemResponse,
    TransactionsHistoryResponse,
)
from technical_document_ml_service.services.billing_service import get_user_transactions
from technical_document_ml_service.services.history_service import (
    get_user_prediction_history,
)


router = APIRouter(prefix="/history", tags=["history"])


@router.get("/transactions", response_model=TransactionsHistoryResponse)
def get_transactions_history(
    session: SessionDep,
    current_user: CurrentUserDep,
    pagination: Annotated[PaginationParams, Depends()],
) -> TransactionsHistoryResponse:
    """получить историю транзакций пользователя"""
    items = get_user_transactions(
        session,
        user_id=current_user.id,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    return TransactionsHistoryResponse(
        items=[
            TransactionHistoryItemResponse.from_item(item)
            for item in items
        ],
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get("/predictions", response_model=PredictionsHistoryResponse)
def get_predictions_history(
    session: SessionDep,
    current_user: CurrentUserDep,
    pagination: Annotated[PaginationParams, Depends()],
) -> PredictionsHistoryResponse:
    """получить историю ML-запросов / предсказаний пользователя"""
    items = get_user_prediction_history(
        session,
        user_id=current_user.id,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    return PredictionsHistoryResponse(
        items=[
            PredictionHistoryItemResponse.from_item(item)
            for item in items
        ],
        limit=pagination.limit,
        offset=pagination.offset,
    )