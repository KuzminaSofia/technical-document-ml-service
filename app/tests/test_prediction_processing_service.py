from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select

from technical_document_ml_service.db.models import (
    MLRequestHistoryORM,
    MLTaskORM,
    PredictionResultORM,
    TransactionORM,
    UserORM,
)
from technical_document_ml_service.db.session import SessionLocal
from technical_document_ml_service.services.document_storage_service import (
    IncomingDocumentData,
)
from technical_document_ml_service.services.prediction_processing_service import (
    process_document_prediction_task,
)
from technical_document_ml_service.services.prediction_submission_service import (
    submit_document_prediction,
)


def _submit_test_task(api_user, api_model):
    with SessionLocal() as session:
        submission = submit_document_prediction(
            session,
            user_id=api_user.id,
            model_name=api_model.name,
            target_schema="passport_fields",
            documents=[
                IncomingDocumentData(
                    filename="sample.pdf",
                    content_type="application/pdf",
                    content=b"%PDF-1.4 test content",
                )
            ],
        )

    return submission


def test_process_document_prediction_task_completes_and_persists_result(
    api_user,
    api_model,
    publish_task_spy,
) -> None:
    submission = _submit_test_task(api_user, api_model)

    with SessionLocal() as session:
        result = process_document_prediction_task(
            session,
            task_id=submission.task_id,
        )

    assert result.task_id == submission.task_id
    assert result.status.value == "completed"
    assert result.was_processed is True
    assert result.result_id is not None
    assert result.spent_credits == Decimal("10.00")
    assert result.completed_at is not None

    assert len(publish_task_spy) == 1

    with SessionLocal() as session:
        task = session.get(MLTaskORM, submission.task_id)
        assert task is not None
        assert task.status == "completed"
        assert task.spent_credits == Decimal("10.00")
        assert task.completed_at is not None

        user = session.get(UserORM, api_user.id)
        assert user is not None
        assert user.balance_credits == Decimal("90.00")

        prediction_results_count = session.scalar(
            select(func.count()).select_from(PredictionResultORM)
        )
        transactions_count = session.scalar(
            select(func.count()).select_from(TransactionORM)
        )
        history_count = session.scalar(
            select(func.count()).select_from(MLRequestHistoryORM)
        )

        assert prediction_results_count == 1
        assert transactions_count == 1
        assert history_count == 1


def test_process_document_prediction_task_is_idempotent_for_completed_task(
    api_user,
    api_model,
    publish_task_spy,
) -> None:
    submission = _submit_test_task(api_user, api_model)

    with SessionLocal() as session:
        first_result = process_document_prediction_task(
            session,
            task_id=submission.task_id,
        )

    assert first_result.was_processed is True

    with SessionLocal() as session:
        second_result = process_document_prediction_task(
            session,
            task_id=submission.task_id,
        )

    assert second_result.task_id == submission.task_id
    assert second_result.status.value == "completed"
    assert second_result.was_processed is False
    assert second_result.message == "Задача уже была успешно обработана ранее."

    with SessionLocal() as session:
        prediction_results_count = session.scalar(
            select(func.count()).select_from(PredictionResultORM)
        )
        transactions_count = session.scalar(
            select(func.count()).select_from(TransactionORM)
        )
        history_count = session.scalar(
            select(func.count()).select_from(MLRequestHistoryORM)
        )

        assert prediction_results_count == 1
        assert transactions_count == 1
        assert history_count == 1