from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from technical_document_ml_service.db.models import TransactionORM
from technical_document_ml_service.domain.enums import TransactionType
from technical_document_ml_service.domain.exceptions import DomainError, InsufficientBalanceError
from technical_document_ml_service.services.billing_service import (
    credit_balance,
    debit_balance,
    get_user_transactions,
)


def test_credit_balance_updates_balance_and_creates_transaction(
    session_factory,
    persisted_user,
) -> None:
    with session_factory.begin() as session:
        new_balance, transaction = credit_balance(
            session,
            user_id=persisted_user.id,
            amount=Decimal("25.50"),
        )

    assert new_balance == Decimal("125.50")
    assert transaction.user_id == persisted_user.id
    assert transaction.transaction_type == TransactionType.CREDIT
    assert transaction.amount == Decimal("25.50")

    with session_factory() as session:
        transactions = get_user_transactions(session, user_id=persisted_user.id)

    assert len(transactions) == 1
    assert transactions[0].transaction_type == TransactionType.CREDIT
    assert transactions[0].amount == Decimal("25.50")


def test_debit_balance_updates_balance_and_creates_transaction(
    session_factory,
    persisted_user,
) -> None:
    with session_factory.begin() as session:
        new_balance, transaction = debit_balance(
            session,
            user_id=persisted_user.id,
            amount=Decimal("30.00"),
        )

    assert new_balance == Decimal("70.00")
    assert transaction.user_id == persisted_user.id
    assert transaction.transaction_type == TransactionType.DEBIT
    assert transaction.amount == Decimal("30.00")

    with session_factory() as session:
        transactions = get_user_transactions(session, user_id=persisted_user.id)

    assert len(transactions) == 1
    assert transactions[0].transaction_type == TransactionType.DEBIT
    assert transactions[0].amount == Decimal("30.00")


def test_debit_balance_raises_when_insufficient_funds(
    session_factory,
    persisted_user,
) -> None:
    with pytest.raises(InsufficientBalanceError):
        with session_factory.begin() as session:
            debit_balance(
                session,
                user_id=persisted_user.id,
                amount=Decimal("1000.00"),
            )

    with session_factory() as session:
        transactions = get_user_transactions(session, user_id=persisted_user.id)

    assert transactions == []


def test_get_user_transactions_returns_reverse_chronological_order(
    session_factory,
    persisted_user,
) -> None:
    older = datetime.now(UTC) - timedelta(days=1)
    newer = datetime.now(UTC)

    with session_factory.begin() as session:
        session.add_all(
            [
                TransactionORM(
                    id=uuid4(),
                    user_id=persisted_user.id,
                    task_id=None,
                    transaction_type=TransactionType.CREDIT.value,
                    amount=Decimal("10.00"),
                    created_at=older,
                ),
                TransactionORM(
                    id=uuid4(),
                    user_id=persisted_user.id,
                    task_id=None,
                    transaction_type=TransactionType.DEBIT.value,
                    amount=Decimal("5.00"),
                    created_at=newer,
                ),
            ]
        )

    with session_factory() as session:
        transactions = get_user_transactions(session, user_id=persisted_user.id)

    assert len(transactions) == 2
    assert transactions[0].created_at == newer
    assert transactions[1].created_at == older
    assert transactions[0].transaction_type == TransactionType.DEBIT
    assert transactions[1].transaction_type == TransactionType.CREDIT


def test_credit_balance_raises_for_nonexistent_user(session_factory) -> None:
    with pytest.raises(DomainError):
        with session_factory.begin() as session:
            credit_balance(session, user_id=uuid4(), amount=Decimal("10.00"))


def test_debit_balance_raises_for_nonexistent_user(session_factory) -> None:
    with pytest.raises(DomainError):
        with session_factory.begin() as session:
            debit_balance(session, user_id=uuid4(), amount=Decimal("10.00"))