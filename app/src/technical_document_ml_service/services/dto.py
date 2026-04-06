from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from technical_document_ml_service.domain.enums import TaskStatus, TransactionType


@dataclass(frozen=True, slots=True)
class TransactionHistoryItem:
    """элемент истории транзакций пользователя"""

    id: UUID
    user_id: UUID
    task_id: UUID | None
    transaction_type: TransactionType
    amount: Decimal
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PredictionHistoryItem:
    """элемент истории ML-запросов / предсказаний пользователя"""

    id: UUID
    user_id: UUID
    task_id: UUID | None
    model_id: UUID
    result_id: UUID | None
    status: TaskStatus
    spent_credits: Decimal
    created_at: datetime
    completed_at: datetime | None