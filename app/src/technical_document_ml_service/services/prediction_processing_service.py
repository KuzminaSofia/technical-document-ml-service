from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from technical_document_ml_service.db.models import MLTaskORM, UploadedDocumentORM
from technical_document_ml_service.domain.entities import (
    DocumentExtractionTask,
    UploadedDocument,
)
from technical_document_ml_service.domain.enums import DocumentType, TaskStatus
from technical_document_ml_service.domain.exceptions import NotFoundError
from technical_document_ml_service.services.billing_service import record_transaction
from technical_document_ml_service.services.history_service import (
    create_history_record_from_task,
)
from technical_document_ml_service.services.mappers import (
    orm_to_domain_user,
    sync_task_orm_from_domain,
    sync_user_orm_from_domain,
)
from technical_document_ml_service.services.prediction_service import (
    model_orm_to_domain,
    persist_prediction_result,
)


@dataclass(frozen=True, slots=True)
class PredictionProcessingResult:
    """результат обработки задачи воркером"""

    task_id: UUID
    status: TaskStatus
    result_id: UUID | None
    created_at: datetime
    completed_at: datetime | None
    spent_credits: Decimal
    was_processed: bool
    message: str


def _parse_document_type(raw_value: str) -> DocumentType:
    """безопасно преобразовать строковый тип документа в enum"""
    try:
        return DocumentType(raw_value)
    except ValueError:
        return DocumentType.UNKNOWN


def _document_orm_to_domain(document_orm: UploadedDocumentORM) -> UploadedDocument:
    """преобразовать ORM-документ в доменную сущность"""
    return UploadedDocument(
        owner_id=document_orm.owner_id,
        original_filename=document_orm.filename,
        storage_path=document_orm.storage_path,
        mime_type=document_orm.mime_type,
        document_type=_parse_document_type(document_orm.document_type),
        size_bytes=document_orm.file_size,
        entity_id=document_orm.id,
        uploaded_at=document_orm.uploaded_at,
    )


def _task_orm_to_domain(task_orm: MLTaskORM) -> DocumentExtractionTask:
    """преобразовать ORM-задачу в доменную задачу извлечения документов"""
    result_id = None
    if task_orm.prediction_result is not None:
        result_id = task_orm.prediction_result.id

    return DocumentExtractionTask(
        user_id=task_orm.user_id,
        model_id=task_orm.model_id,
        documents=[_document_orm_to_domain(document) for document in task_orm.documents],
        target_schema=task_orm.target_schema or "",
        entity_id=task_orm.id,
        status=TaskStatus(task_orm.status),
        created_at=task_orm.created_at,
        started_at=task_orm.started_at,
        finished_at=task_orm.completed_at,
        error_message=task_orm.error_message,
        spent_credits=task_orm.spent_credits,
        result_id=result_id,
    )


def _load_task_for_processing(session: Session, task_id: UUID) -> MLTaskORM | None:
    """загрузить задачу и все необходимые связи с блокировкой строки"""
    statement = (
        select(MLTaskORM)
        .where(MLTaskORM.id == task_id)
        .options(
            selectinload(MLTaskORM.user),
            selectinload(MLTaskORM.model),
            selectinload(MLTaskORM.documents),
            selectinload(MLTaskORM.prediction_result),
        )
        .with_for_update()
    )

    return session.execute(statement).scalar_one_or_none()


def _build_skipped_result(
    task_orm: MLTaskORM,
    *,
    message: str,
) -> PredictionProcessingResult:
    """сформировать результат, если повторная обработка не требуется"""
    result_id = None
    if task_orm.prediction_result is not None:
        result_id = task_orm.prediction_result.id

    return PredictionProcessingResult(
        task_id=task_orm.id,
        status=TaskStatus(task_orm.status),
        result_id=result_id,
        created_at=task_orm.created_at,
        completed_at=task_orm.completed_at,
        spent_credits=task_orm.spent_credits,
        was_processed=False,
        message=message,
    )


def _mark_task_as_failed(
    session: Session,
    *,
    task_id: UUID,
    error_message: str,
) -> None:
    """зафиксировать ошибку обработки задачи в БД"""
    persisted_task_orm = _load_task_for_processing(session, task_id)
    if persisted_task_orm is None:
        return

    domain_task = _task_orm_to_domain(persisted_task_orm)
    domain_task.fail(error_message)
    sync_task_orm_from_domain(persisted_task_orm, domain_task)
    session.commit()


def process_document_prediction_task(
    session: Session,
    *,
    task_id: UUID,
) -> PredictionProcessingResult:
    """
    обработать ранее поставленную в очередь задачу

    Сценарий:
    1. загрузить задачу и связанные данные;
    2. проверить, нужно ли её реально обрабатывать;
    3. восстановить доменные объекты;
    4. выполнить задачу;
    5. сохранить результат, транзакцию и историю.
    """
    task_orm = _load_task_for_processing(session, task_id)
    if task_orm is None:
        raise NotFoundError(f"Задача с id={task_id} не найдена.")

    current_status = TaskStatus(task_orm.status)

    if current_status == TaskStatus.COMPLETED:
        return _build_skipped_result(
            task_orm,
            message="Задача уже была успешно обработана ранее.",
        )

    if current_status == TaskStatus.PROCESSING:
        return _build_skipped_result(
            task_orm,
            message="Задача уже находится в обработке.",
        )

    if current_status == TaskStatus.VALIDATING:
        return _build_skipped_result(
            task_orm,
            message="Задача уже находится на этапе валидации.",
        )

    if current_status == TaskStatus.FAILED:
        return _build_skipped_result(
            task_orm,
            message="Задача ранее завершилась с ошибкой.",
        )

    if current_status != TaskStatus.QUEUED:
        return _build_skipped_result(
            task_orm,
            message=(
                f"Задача в статусе {current_status.value} "
                "не может быть обработана воркером."
            ),
        )

    domain_user = orm_to_domain_user(task_orm.user)
    domain_model = model_orm_to_domain(task_orm.model)
    domain_task = _task_orm_to_domain(task_orm)

    try:
        result, debit_transaction = domain_task.run(domain_user, domain_model)

        sync_user_orm_from_domain(task_orm.user, domain_user)
        sync_task_orm_from_domain(task_orm, domain_task)

        persist_prediction_result(
            session,
            task_id=domain_task.id,
            result=result,
        )
        record_transaction(
            session,
            transaction=debit_transaction,
        )
        create_history_record_from_task(session, domain_task)

        session.commit()

        return PredictionProcessingResult(
            task_id=domain_task.id,
            status=domain_task.status,
            result_id=domain_task.result_id,
            created_at=domain_task.created_at,
            completed_at=domain_task.finished_at,
            spent_credits=domain_task.spent_credits,
            was_processed=True,
            message="Задача успешно обработана.",
        )

    except Exception as exc:
        if session.in_transaction():
            session.rollback()

        _mark_task_as_failed(
            session,
            task_id=task_id,
            error_message=str(exc),
        )
        raise