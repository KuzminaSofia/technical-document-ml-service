from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from technical_document_ml_service.db.models import TransactionORM, UserORM
from technical_document_ml_service.domain.entities import CreditTransaction, DebitTransaction
from technical_document_ml_service.domain.exceptions import NotFoundError
from technical_document_ml_service.services.dto import TransactionHistoryItem
from technical_document_ml_service.services.mappers import (
    orm_to_domain_user,
    sync_user_orm_from_domain,
    transaction_orm_to_item,
)


def _get_user_orm_or_raise(session: Session, user_id: UUID) -> UserORM:
    user_orm = session.get(UserORM, user_id)
    if user_orm is None:
        raise NotFoundError("Пользователь не найден.")
    return user_orm


def _persist_transaction(
    session: Session,
    *,
    transaction_id: UUID,
    user_id: UUID,
    task_id: UUID | None,
    transaction_type: str,
    amount: Decimal,
    created_at,
) -> TransactionORM:
    transaction_orm = TransactionORM(
        id=transaction_id,
        user_id=user_id,
        task_id=task_id,
        transaction_type=transaction_type,
        amount=amount,
        created_at=created_at,
    )
    session.add(transaction_orm)
    return transaction_orm


def credit_balance(
    session: Session,
    *,
    user_id: UUID,
    amount: Decimal,
    task_id: UUID | None = None,
) -> tuple[Decimal, TransactionHistoryItem]:
    """
    пополнить баланс пользователя и записать транзакцию
    возвращает новый баланс и DTO созданной транзакции
    """
    user_orm = _get_user_orm_or_raise(session, user_id)
    domain_user = orm_to_domain_user(user_orm)

    transaction = CreditTransaction(
        user_id=user_id,
        amount=amount,
        task_id=task_id,
    )
    transaction.apply(domain_user)

    sync_user_orm_from_domain(user_orm, domain_user)

    transaction_orm = _persist_transaction(
        session,
        transaction_id=transaction.id,
        user_id=transaction.user_id,
        task_id=transaction.task_id,
        transaction_type=transaction.transaction_type.value,
        amount=transaction.amount,
        created_at=transaction.created_at,
    )

    session.flush()

    return user_orm.balance_credits, transaction_orm_to_item(transaction_orm)


def debit_balance(
    session: Session,
    *,
    user_id: UUID,
    amount: Decimal,
    task_id: UUID | None = None,
) -> tuple[Decimal, TransactionHistoryItem]:
    """
    списать средства с баланса пользователя и записать транзакцию
    доменные исключения наружу:
    - InvalidAmountError
    - InsufficientBalanceError
    - NotFoundError
    """
    user_orm = _get_user_orm_or_raise(session, user_id)
    domain_user = orm_to_domain_user(user_orm)

    transaction = DebitTransaction(
        user_id=user_id,
        amount=amount,
        task_id=task_id,
    )
    transaction.apply(domain_user)

    sync_user_orm_from_domain(user_orm, domain_user)

    transaction_orm = _persist_transaction(
        session,
        transaction_id=transaction.id,
        user_id=transaction.user_id,
        task_id=transaction.task_id,
        transaction_type=transaction.transaction_type.value,
        amount=transaction.amount,
        created_at=transaction.created_at,
    )

    session.flush()

    return user_orm.balance_credits, transaction_orm_to_item(transaction_orm)


def get_user_transactions(
    session: Session,
    *,
    user_id: UUID,
    limit: int | None = None,
    offset: int = 0,
) -> list[TransactionHistoryItem]:
    """
    получить историю транзакций пользователя в обратном хронологическом порядке
    """
    statement = (
        select(TransactionORM)
        .where(TransactionORM.user_id == user_id)
        .order_by(TransactionORM.created_at.desc())
        .offset(offset)
    )

    if limit is not None:
        statement = statement.limit(limit)

    transactions = session.scalars(statement).all()
    return [transaction_orm_to_item(transaction) for transaction in transactions]