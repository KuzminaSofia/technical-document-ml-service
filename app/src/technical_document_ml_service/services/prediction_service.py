from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from technical_document_ml_service.db.models import (
    MLModelORM,
    MLTaskORM,
    PredictionResultORM,
    UploadedDocumentORM,
)
from technical_document_ml_service.domain.entities import (
    DocumentExtractionTask,
    PredictionResult,
    TechnicalDocumentExtractionModel,
    UploadedDocument,
    User,
    ValidationIssue,
)
from technical_document_ml_service.domain.enums import DocumentType, TaskStatus
from technical_document_ml_service.domain.exceptions import (
    InsufficientBalanceError,
    ModelUnavailableError,
    TaskExecutionError,
)
from technical_document_ml_service.services.billing_service import record_transaction
from technical_document_ml_service.services.document_storage_service import (
    IncomingDocumentData,
    StoredDocumentData,
    delete_stored_files,
    save_documents,
)
from technical_document_ml_service.services.history_service import (
    create_history_record_from_task,
)
from technical_document_ml_service.services.mappers import (
    orm_to_domain_user,
    sync_user_orm_from_domain,
)
from technical_document_ml_service.services.orm_queries import (
    get_model_orm_by_name_or_raise,
    get_user_orm_or_raise,
)


@dataclass(frozen=True, slots=True)
class PredictionExecutionResult:
    """результат выполнения запроса на предсказание"""

    task_id: UUID
    model_id: UUID
    model_name: str
    status: TaskStatus
    spent_credits: Decimal
    remaining_balance_credits: Decimal
    result_id: UUID | None
    created_at: datetime
    completed_at: datetime | None
    extracted_data: dict[str, Any]
    validation_issues: list[ValidationIssue]
    output_path: str | None


def _parse_supported_document_types(values: list[str]) -> set[DocumentType]:
    """преобразовать список строковых типов документов в enum-значения"""
    parsed: set[DocumentType] = set()

    for value in values:
        try:
            parsed.add(DocumentType(value))
        except ValueError:
            continue

    if not parsed:
        parsed.add(DocumentType.UNKNOWN)

    return parsed


def model_orm_to_domain(model_orm: MLModelORM) -> TechnicalDocumentExtractionModel:
    """преобразовать ORM-модель в доменную ML-модель"""
    if model_orm.model_kind != "technical_document_extraction":
        raise TaskExecutionError("Неподдерживаемый тип ML-модели.")

    return TechnicalDocumentExtractionModel(
        name=model_orm.name,
        description=model_orm.description,
        prediction_cost=model_orm.prediction_cost,
        supported_document_types=_parse_supported_document_types(
            model_orm.supported_document_types
        ),
        is_active=model_orm.is_active,
        entity_id=model_orm.id,
    )


def build_domain_documents(
    *,
    owner_id: UUID,
    stored_documents: list[StoredDocumentData],
) -> list[UploadedDocument]:
    """создать доменные объекты загруженных документов"""
    domain_documents: list[UploadedDocument] = []

    for stored_document in stored_documents:
        domain_documents.append(
            UploadedDocument(
                owner_id=owner_id,
                original_filename=stored_document.original_filename,
                storage_path=stored_document.storage_path,
                mime_type=stored_document.mime_type,
                document_type=DocumentType.UNKNOWN,
                size_bytes=stored_document.size_bytes,
            )
        )

    return domain_documents


def persist_uploaded_documents(
    session: Session,
    *,
    documents: list[UploadedDocument],
) -> list[UploadedDocumentORM]:
    """сохранить документы в БД"""
    document_orms: list[UploadedDocumentORM] = []

    for document in documents:
        document_orm = UploadedDocumentORM(
            id=document.id,
            owner_id=document.owner_id,
            filename=document.original_filename,
            storage_path=document.storage_path,
            mime_type=document.mime_type,
            document_type=document.document_type.value,
            file_size=document.size_bytes,
            uploaded_at=document.uploaded_at,
        )
        session.add(document_orm)
        document_orms.append(document_orm)

    return document_orms


def persist_task(
    session: Session,
    *,
    task: DocumentExtractionTask,
    document_orms: list[UploadedDocumentORM],
) -> MLTaskORM:
    """сохранить ML-задачу и её связь с документами"""
    task_orm = MLTaskORM(
        id=task.id,
        user_id=task.user_id,
        model_id=task.model_id,
        status=task.status.value,
        spent_credits=task.spent_credits,
        target_schema=task.target_schema,
        error_message=task.error_message,
        started_at=task.started_at,
        completed_at=task.finished_at,
        created_at=task.created_at,
    )
    session.add(task_orm)
    session.flush()

    task_orm.documents.extend(document_orms)
    return task_orm


def persist_prediction_result(
    session: Session,
    *,
    task_id: UUID,
    result: PredictionResult,
) -> PredictionResultORM:
    """сохранить результат предсказания"""
    validation_issues_payload = [
        {
            "field_name": issue.field_name,
            "message": issue.message,
            "raw_value": issue.raw_value,
        }
        for issue in result.validation_issues
    ]

    result_orm = PredictionResultORM(
        id=result.id,
        task_id=task_id,
        extracted_data=result.extracted_data,
        validation_issues=validation_issues_payload,
        output_file_path=result.output_path,
        created_at=result.created_at,
    )
    session.add(result_orm)
    session.flush()

    return result_orm


def ensure_prediction_can_start(
    *,
    user: User,
    model: TechnicalDocumentExtractionModel,
) -> None:
    """
    выполнить ранние проверки до сохранения файлов на диск и создания артефактов
    """
    if not model.is_active:
        raise ModelUnavailableError("Выбранная ML-модель недоступна.")

    if not user.can_afford(model.prediction_cost):
        raise InsufficientBalanceError("Недостаточно средств для выполнения задачи.")


def execute_document_prediction(
    session: Session,
    *,
    user_id: UUID,
    model_name: str,
    target_schema: str,
    documents: list[IncomingDocumentData],
) -> PredictionExecutionResult:
    """
    выполнить полный пользовательский сценарий предсказания:
    - выбрать модель;
    - сохранить документы;
    - создать доменную задачу;
    - выполнить задачу;
    - сохранить задачу, результат, транзакцию и историю
    """
    saved_paths: list[str] = []

    try:
        user_orm = get_user_orm_or_raise(session, user_id)
        model_orm = get_model_orm_by_name_or_raise(session, model_name)

        domain_user = orm_to_domain_user(user_orm)
        domain_model = model_orm_to_domain(model_orm)

        ensure_prediction_can_start(
            user=domain_user,
            model=domain_model,
        )

        stored_documents = save_documents(
            owner_id=user_id,
            documents=documents,
        )
        saved_paths = [document.storage_path for document in stored_documents]

        domain_documents = build_domain_documents(
            owner_id=user_id,
            stored_documents=stored_documents,
        )

        task = DocumentExtractionTask(
            user_id=user_id,
            model_id=domain_model.id,
            documents=domain_documents,
            target_schema=target_schema,
        )

        result, debit_transaction = task.run(domain_user, domain_model)

        sync_user_orm_from_domain(user_orm, domain_user)

        document_orms = persist_uploaded_documents(
            session,
            documents=domain_documents,
        )
        persist_task(
            session,
            task=task,
            document_orms=document_orms,
        )
        persist_prediction_result(
            session,
            task_id=task.id,
            result=result,
        )
        record_transaction(
            session,
            transaction=debit_transaction,
        )
        create_history_record_from_task(session, task)

        return PredictionExecutionResult(
            task_id=task.id,
            model_id=domain_model.id,
            model_name=domain_model.name,
            status=task.status,
            spent_credits=task.spent_credits,
            remaining_balance_credits=domain_user.balance_credits,
            result_id=task.result_id,
            created_at=task.created_at,
            completed_at=task.finished_at,
            extracted_data=result.extracted_data,
            validation_issues=result.validation_issues,
            output_path=result.output_path,
        )

    except Exception:
        if saved_paths:
            delete_stored_files(saved_paths)
        raise