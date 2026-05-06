from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from technical_document_ml_service.domain.entities import ValidationIssue
from technical_document_ml_service.domain.enums import TaskStatus


class ValidationIssueResponse(BaseModel):
    """ошибка или замечание, найденное при валидации входных данных"""

    field_name: str
    message: str
    raw_value: Any | None

    @classmethod
    def from_domain(cls, issue: ValidationIssue) -> "ValidationIssueResponse":
        return cls(
            field_name=issue.field_name,
            message=issue.message,
            raw_value=issue.raw_value,
        )


class PredictAcceptedResponse(BaseModel):
    """
    ответ API при асинхронной постановке задачи:
    запрос принят, задача сохранена и отправлена в очередь
    """

    task_id: UUID
    model_id: UUID
    model_name: str
    status: TaskStatus
    created_at: datetime
    callback_url: str | None
    message: str

    @classmethod
    def create(
        cls,
        *,
        task_id: UUID,
        model_id: UUID,
        model_name: str,
        created_at: datetime,
        callback_url: str | None = None,
        message: str = "Задача принята и поставлена в очередь на обработку.",
    ) -> "PredictAcceptedResponse":
        return cls(
            task_id=task_id,
            model_id=model_id,
            model_name=model_name,
            status=TaskStatus.QUEUED,
            created_at=created_at,
            callback_url=callback_url,
            message=message,
        )
