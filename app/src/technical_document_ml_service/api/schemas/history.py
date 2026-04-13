from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from technical_document_ml_service.domain.enums import TaskStatus, TransactionType
from technical_document_ml_service.services.dto import (
    PredictionHistoryItem,
    TransactionHistoryItem,
)


class PaginationParams(BaseModel):
    """параметры пагинации для истории"""

    limit: int | None = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class TransactionHistoryItemResponse(BaseModel):
    """элемент истории транзакций"""

    id: UUID
    user_id: UUID
    task_id: UUID | None
    transaction_type: TransactionType
    amount: Decimal
    created_at: datetime

    @classmethod
    def from_item(
        cls,
        item: TransactionHistoryItem,
    ) -> "TransactionHistoryItemResponse":
        return cls(
            id=item.id,
            user_id=item.user_id,
            task_id=item.task_id,
            transaction_type=item.transaction_type,
            amount=item.amount,
            created_at=item.created_at,
        )


class PredictionHistoryItemResponse(BaseModel):
    """элемент истории ML-запросов / предсказаний"""

    id: UUID
    user_id: UUID
    task_id: UUID | None
    model_id: UUID
    result_id: UUID | None
    status: TaskStatus
    spent_credits: Decimal
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_item(
        cls,
        item: PredictionHistoryItem,
    ) -> "PredictionHistoryItemResponse":
        return cls(
            id=item.id,
            user_id=item.user_id,
            task_id=item.task_id,
            model_id=item.model_id,
            result_id=item.result_id,
            status=item.status,
            spent_credits=item.spent_credits,
            created_at=item.created_at,
            completed_at=item.completed_at,
        )


class TransactionsHistoryResponse(BaseModel):
    """ответ со списком транзакций пользователя"""

    items: list[TransactionHistoryItemResponse]
    limit: int | None
    offset: int


class PredictionsHistoryResponse(BaseModel):
    """ответ со списком ML-запросов пользователя"""

    items: list[PredictionHistoryItemResponse]
    limit: int | None
    offset: int