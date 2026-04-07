from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from technical_document_ml_service.db.models import MLRequestHistoryORM, MLTaskORM
from technical_document_ml_service.domain.entities import DocumentExtractionTask
from technical_document_ml_service.domain.enums import TaskStatus
from technical_document_ml_service.services.history_service import (
    create_history_record_from_task,
    get_user_prediction_history,
)


def test_create_history_record_from_task_persists_record(
    session_factory,
    persisted_user,
    persisted_model,
) -> None:
    task_id = uuid4()

    with session_factory.begin() as session:
        session.add(
            MLTaskORM(
                id=task_id,
                user_id=persisted_user.id,
                model_id=persisted_model.id,
                status=TaskStatus.CREATED.value,
                spent_credits=Decimal("0.00"),
                target_schema="test_schema",
                error_message=None,
            )
        )

        domain_task = DocumentExtractionTask(
            user_id=persisted_user.id,
            model_id=persisted_model.id,
            documents=[],
            target_schema="test_schema",
            entity_id=task_id,
        )

        created_record = create_history_record_from_task(session, domain_task)

    assert created_record.user_id == persisted_user.id
    assert created_record.task_id == task_id
    assert created_record.model_id == persisted_model.id
    assert created_record.status == TaskStatus.CREATED
    assert created_record.spent_credits == Decimal("0")

    with session_factory() as session:
        history = get_user_prediction_history(session, user_id=persisted_user.id)

    assert len(history) == 1
    assert history[0].task_id == task_id
    assert history[0].status == TaskStatus.CREATED


def test_get_user_prediction_history_returns_reverse_chronological_order(
    session_factory,
    persisted_user,
    persisted_model,
) -> None:
    task_id_1 = uuid4()
    task_id_2 = uuid4()

    older = datetime.now(UTC) - timedelta(days=1)
    newer = datetime.now(UTC)

    with session_factory.begin() as session:
        session.add_all(
            [
                MLTaskORM(
                    id=task_id_1,
                    user_id=persisted_user.id,
                    model_id=persisted_model.id,
                    status=TaskStatus.COMPLETED.value,
                    spent_credits=Decimal("10.00"),
                    target_schema="schema_1",
                    error_message=None,
                    created_at=older,
                    completed_at=older,
                ),
                MLTaskORM(
                    id=task_id_2,
                    user_id=persisted_user.id,
                    model_id=persisted_model.id,
                    status=TaskStatus.COMPLETED.value,
                    spent_credits=Decimal("20.00"),
                    target_schema="schema_2",
                    error_message=None,
                    created_at=newer,
                    completed_at=newer,
                ),
            ]
        )

        session.add_all(
            [
                MLRequestHistoryORM(
                    id=uuid4(),
                    user_id=persisted_user.id,
                    task_id=task_id_1,
                    model_id=persisted_model.id,
                    result_id=None,
                    status=TaskStatus.COMPLETED.value,
                    spent_credits=Decimal("10.00"),
                    created_at=older,
                    completed_at=older,
                ),
                MLRequestHistoryORM(
                    id=uuid4(),
                    user_id=persisted_user.id,
                    task_id=task_id_2,
                    model_id=persisted_model.id,
                    result_id=None,
                    status=TaskStatus.COMPLETED.value,
                    spent_credits=Decimal("20.00"),
                    created_at=newer,
                    completed_at=newer,
                ),
            ]
        )

    with session_factory() as session:
        history = get_user_prediction_history(session, user_id=persisted_user.id)

    assert len(history) == 2
    assert history[0].task_id == task_id_2
    assert history[1].task_id == task_id_1
    assert history[0].created_at == newer
    assert history[1].created_at == older
    assert history[0].spent_credits == Decimal("20.00")
    assert history[1].spent_credits == Decimal("10.00")