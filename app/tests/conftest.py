from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text

from technical_document_ml_service.db.base import Base
from technical_document_ml_service.db.models import MLModelORM, UserORM
from technical_document_ml_service.db.session import SessionLocal, engine
from technical_document_ml_service.domain.enums import UserRole


@pytest.fixture(scope="session", autouse=True)
def prepare_database() -> None:
    """
    гарантирует, что таблицы существуют перед запуском тестов
    """
    Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_database() -> None:
    """
    очищает все таблицы до и после каждого теста
    """
    table_names = ", ".join(table.name for table in reversed(Base.metadata.sorted_tables))
    truncate_sql = text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE")

    with engine.begin() as connection:
        connection.execute(truncate_sql)

    yield

    with engine.begin() as connection:
        connection.execute(truncate_sql)


@pytest.fixture
def session_factory():
    """фабрика сессий для тестов"""
    return SessionLocal


@pytest.fixture
def persisted_user(session_factory) -> UserORM:
    """
    создает и сохраняет пользователя через ORM для тестовых сценариев
    """
    with session_factory.begin() as session:
        user = UserORM(
            id=uuid4(),
            email="persisted.user@example.com",
            password_hash="hashed-password",
            role=UserRole.USER.value,
            balance_credits=Decimal("100.00"),
            is_active=True,
        )
        session.add(user)
        session.flush()
        user_id = user.id

    with session_factory() as session:
        return session.get(UserORM, user_id)


@pytest.fixture
def persisted_model(session_factory) -> MLModelORM:
    """
    создает и сохраняет ML-модель напрямую через ORM для тестовых сценариев
    """
    with session_factory.begin() as session:
        model = MLModelORM(
            id=uuid4(),
            name="test-model",
            description="Тестовая модель",
            prediction_cost=Decimal("10.00"),
            is_active=True,
            model_kind="technical_document_extraction",
            supported_document_types=["unknown"],
        )
        session.add(model)
        session.flush()
        model_id = model.id

    with session_factory() as session:
        return session.get(MLModelORM, model_id)