from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from technical_document_ml_service.db.models import MLRequestHistoryORM
from technical_document_ml_service.domain.entities import MLRequestHistoryRecord, MLTask
from technical_document_ml_service.services.dto import PredictionHistoryItem
from technical_document_ml_service.services.mappers import (
    domain_history_to_orm,
    history_orm_to_item,
)


def create_history_record_from_task(
    session: Session,
    task: MLTask,
) -> PredictionHistoryItem:
    """
    создать и сохранить запись истории ML-запроса на основе доменной задачи
    """
    domain_record = MLRequestHistoryRecord.from_task(task)
    history_orm = domain_history_to_orm(domain_record)

    session.add(history_orm)
    session.flush()

    return history_orm_to_item(history_orm)


def get_user_prediction_history(
    session: Session,
    *,
    user_id: UUID,
    limit: int | None = None,
    offset: int = 0,
) -> list[PredictionHistoryItem]:
    """
    получить историю ML-запросов / предсказаний пользователя
    в обратном хронологическом порядке
    """
    statement = (
        select(MLRequestHistoryORM)
        .where(MLRequestHistoryORM.user_id == user_id)
        .order_by(MLRequestHistoryORM.created_at.desc())
        .offset(offset)
    )

    if limit is not None:
        statement = statement.limit(limit)

    history_records = session.scalars(statement).all()
    return [history_orm_to_item(record) for record in history_records]