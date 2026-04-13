from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from technical_document_ml_service.api.schemas.history import (
    TransactionHistoryItemResponse,
)


class BalanceResponse(BaseModel):
    """ответ с текущим балансом пользователя"""

    user_id: UUID
    balance_credits: Decimal


class TopUpBalanceRequest(BaseModel):
    """тело запроса на пополнение баланса"""

    amount: Decimal = Field(gt=Decimal("0"))


class TopUpBalanceResponse(BaseModel):
    """ответ после успешного пополнения баланса"""

    user_id: UUID
    balance_credits: Decimal
    transaction: TransactionHistoryItemResponse