from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from technical_document_ml_service.domain.entities import ValidationIssue
from technical_document_ml_service.domain.enums import TaskStatus
from technical_document_ml_service.services.prediction_service import (
    PredictionExecutionResult,
)


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


class PredictResponse(BaseModel):
    """ответ успешного выполнения предсказания"""

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
    validation_issues: list[ValidationIssueResponse]
    output_path: str | None

    @classmethod
    def from_execution(
        cls,
        execution: PredictionExecutionResult,
    ) -> "PredictResponse":
        return cls(
            task_id=execution.task_id,
            model_id=execution.model_id,
            model_name=execution.model_name,
            status=execution.status,
            spent_credits=execution.spent_credits,
            remaining_balance_credits=execution.remaining_balance_credits,
            result_id=execution.result_id,
            created_at=execution.created_at,
            completed_at=execution.completed_at,
            extracted_data=execution.extracted_data,
            validation_issues=[
                ValidationIssueResponse.from_domain(issue)
                for issue in execution.validation_issues
            ],
            output_path=execution.output_path,
        )