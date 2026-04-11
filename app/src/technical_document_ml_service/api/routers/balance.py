from __future__ import annotations

from fastapi import APIRouter

from technical_document_ml_service.api.deps import (
    CurrentReadUserDep,
    CurrentUserDep,
    SessionDep,
)
from technical_document_ml_service.api.schemas.balance import (
    BalanceResponse,
    TopUpBalanceRequest,
    TopUpBalanceResponse,
)
from technical_document_ml_service.api.schemas.history import (
    TransactionHistoryItemResponse,
)
from technical_document_ml_service.services.billing_service import credit_balance


router = APIRouter(prefix="/balance", tags=["balance"])


@router.get("", response_model=BalanceResponse)
def get_balance(current_user: CurrentReadUserDep) -> BalanceResponse:
    """получить текущий баланс аутентифицированного пользователя"""
    return BalanceResponse(
        user_id=current_user.id,
        balance_credits=current_user.balance_credits,
    )


@router.post("/top-up", response_model=TopUpBalanceResponse)
def top_up_balance(
    payload: TopUpBalanceRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> TopUpBalanceResponse:
    """пополнить баланс текущего пользователя"""
    new_balance, transaction = credit_balance(
        session,
        user_id=current_user.id,
        amount=payload.amount,
    )

    return TopUpBalanceResponse(
        user_id=current_user.id,
        balance_credits=new_balance,
        transaction=TransactionHistoryItemResponse.from_item(transaction),
    )