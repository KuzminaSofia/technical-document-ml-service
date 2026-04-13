from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from technical_document_ml_service.db.models import TransactionORM
from technical_document_ml_service.domain.entities import (
    CreditTransaction,
    DebitTransaction,
    Transaction,
)
from technical_document_ml_service.services.orm_queries import get_user_orm_or_raise
from technical_document_ml_service.services.dto import TransactionHistoryItem
from technical_document_ml_service.services.mappers import (
    orm_to_domain_user,
    sync_user_orm_from_domain,
    transaction_orm_to_item,
)


def record_transaction(
    session: Session,
    *,
    transaction: Transaction,
) -> TransactionHistoryItem:
    """
    сохранить уже созданную доменную транзакцию в БД
    и вернуть DTO сохраненной записи
    """
    transaction_orm = TransactionORM(
        id=transaction.id,
        user_id=transaction.user_id,
        task_id=transaction.task_id,
        transaction_type=transaction.transaction_type.value,
        amount=transaction.amount,
        created_at=transaction.created_at,
    )
    session.add(transaction_orm)
    session.flush()

    return transaction_orm_to_item(transaction_orm)


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
    user_orm = get_user_orm_or_raise(session, user_id)
    domain_user = orm_to_domain_user(user_orm)

    transaction = CreditTransaction(
        user_id=user_id,
        amount=amount,
        task_id=task_id,
    )
    transaction.apply(domain_user)

    sync_user_orm_from_domain(user_orm, domain_user)
    transaction_item = record_transaction(session, transaction=transaction)

    return user_orm.balance_credits, transaction_item


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
    user_orm = get_user_orm_or_raise(session, user_id)
    domain_user = orm_to_domain_user(user_orm)

    transaction = DebitTransaction(
        user_id=user_id,
        amount=amount,
        task_id=task_id,
    )
    transaction.apply(domain_user)

    sync_user_orm_from_domain(user_orm, domain_user)
    transaction_item = record_transaction(session, transaction=transaction)

    return user_orm.balance_credits, transaction_item


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