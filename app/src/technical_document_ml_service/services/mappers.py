from __future__ import annotations

from technical_document_ml_service.db.models import (
    MLRequestHistoryORM,
    MLTaskORM,
    TransactionORM,
    UserORM,
)
from technical_document_ml_service.domain.entities import MLRequestHistoryRecord, MLTask, User
from technical_document_ml_service.domain.enums import TaskStatus, TransactionType, UserRole
from technical_document_ml_service.services.dto import (
    PredictionHistoryItem,
    TransactionHistoryItem,
)


def orm_to_domain_user(user_orm: UserORM) -> User:
    """
    преобразовать ORM-пользователя в доменную сущность
    """
    return User(
        email=user_orm.email,
        password_hash=user_orm.password_hash,
        role=UserRole(user_orm.role),
        balance_credits=user_orm.balance_credits,
        is_active=user_orm.is_active,
        entity_id=user_orm.id,
        created_at=user_orm.created_at,
    )


def sync_user_orm_from_domain(user_orm: UserORM, user: User) -> None:
    """синхронизировать изменяемые поля ORM-модели пользователя из доменной сущности"""
    user_orm.balance_credits = user.balance_credits
    user_orm.is_active = user.is_active


def sync_task_orm_from_domain(task_orm: MLTaskORM, task: MLTask) -> None:
    """синхронизировать изменяемые поля ORM-задачи из доменной сущности"""
    task_orm.status = task.status.value
    task_orm.spent_credits = task.spent_credits
    task_orm.error_message = task.error_message
    task_orm.started_at = task.started_at
    task_orm.completed_at = task.finished_at


def transaction_orm_to_item(transaction_orm: TransactionORM) -> TransactionHistoryItem:
    """преобразовать ORM-транзакцию в DTO истории"""
    return TransactionHistoryItem(
        id=transaction_orm.id,
        user_id=transaction_orm.user_id,
        task_id=transaction_orm.task_id,
        transaction_type=TransactionType(transaction_orm.transaction_type),
        amount=transaction_orm.amount,
        created_at=transaction_orm.created_at,
    )


def history_orm_to_item(history_orm: MLRequestHistoryORM) -> PredictionHistoryItem:
    """преобразовать ORM-запись истории в DTO истории предиктов"""
    return PredictionHistoryItem(
        id=history_orm.id,
        user_id=history_orm.user_id,
        task_id=history_orm.task_id,
        model_id=history_orm.model_id,
        result_id=history_orm.result_id,
        status=TaskStatus(history_orm.status),
        spent_credits=history_orm.spent_credits,
        created_at=history_orm.created_at,
        completed_at=history_orm.completed_at,
    )


def domain_history_to_orm(record: MLRequestHistoryRecord) -> MLRequestHistoryORM:
    """преобразовать доменную запись истории в ORM-модель"""
    return MLRequestHistoryORM(
        id=record.id,
        user_id=record.user_id,
        task_id=record.task_id,
        model_id=record.model_id,
        result_id=record.result_id,
        status=record.status.value,
        spent_credits=record.spent_credits,
        created_at=record.created_at,
        completed_at=record.completed_at,
    )