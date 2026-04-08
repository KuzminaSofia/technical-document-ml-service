from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from technical_document_ml_service.domain.enums import UserRole
from technical_document_ml_service.domain.exceptions import DomainError
from technical_document_ml_service.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
)


def test_create_user_persists_user(session_factory) -> None:
    with session_factory.begin() as session:
        created_user = create_user(
            session,
            email="new.user@example.com",
            password_hash="hashed-password",
            role=UserRole.USER,
            balance_credits=Decimal("15.00"),
            is_active=True,
        )

    with session_factory() as session:
        loaded_user = get_user_by_email(session, "new.user@example.com")

    assert loaded_user is not None
    assert loaded_user.id == created_user.id
    assert loaded_user.email == "new.user@example.com"
    assert loaded_user.role == UserRole.USER
    assert loaded_user.balance_credits == Decimal("15.00")
    assert loaded_user.is_active is True


def test_get_user_by_id_returns_user(session_factory) -> None:
    with session_factory.begin() as session:
        created_user = create_user(
            session,
            email="id.lookup@example.com",
            password_hash="hashed-password",
            role=UserRole.ADMIN,
            balance_credits=Decimal("50.00"),
        )

    with session_factory() as session:
        loaded_user = get_user_by_id(session, created_user.id)

    assert loaded_user is not None
    assert loaded_user.id == created_user.id
    assert loaded_user.email == "id.lookup@example.com"
    assert loaded_user.role == UserRole.ADMIN


def test_get_user_by_email_returns_none_for_absent_user(session_factory) -> None:
    with session_factory() as session:
        loaded_user = get_user_by_email(session, "absent@example.com")

    assert loaded_user is None


def test_get_user_by_id_returns_none_for_absent_user(session_factory) -> None:
    with session_factory() as session:
        loaded_user = get_user_by_id(session, uuid4())

    assert loaded_user is None


def test_create_user_raises_on_duplicate_email(session_factory) -> None:
    with session_factory.begin() as session:
        create_user(
            session,
            email="duplicate@example.com",
            password_hash="hashed-password",
            role=UserRole.USER,
        )

    with pytest.raises(DomainError):
        with session_factory.begin() as session:
            create_user(
                session,
                email="duplicate@example.com",
                password_hash="other-hash",
                role=UserRole.USER,
            )