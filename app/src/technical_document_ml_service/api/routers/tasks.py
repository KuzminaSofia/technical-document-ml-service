from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from technical_document_ml_service.api.deps import CurrentReadUserDep, ReadSessionDep
from technical_document_ml_service.api.schemas.tasks import (
    TaskDetailsResponse,
    TaskListItemResponse,
    TaskListQueryParams,
    TaskResultResponse,
    TasksListResponse,
)
from technical_document_ml_service.services.task_query_service import (
    get_user_task_details,
    get_user_task_result,
    get_user_tasks,
)


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TasksListResponse)
def get_tasks(
    session: ReadSessionDep,
    current_user: CurrentReadUserDep,
    query: Annotated[TaskListQueryParams, Depends()],
) -> TasksListResponse:
    """получить список задач пользователя"""
    items = get_user_tasks(
        session,
        user_id=current_user.id,
        limit=query.limit,
        offset=query.offset,
        status=query.status,
    )

    return TasksListResponse(
        items=[
            TaskListItemResponse.from_item(item)
            for item in items
        ],
        limit=query.limit,
        offset=query.offset,
        status=query.status,
    )


@router.get("/{task_id}", response_model=TaskDetailsResponse)
def get_task_details(
    task_id: UUID,
    session: ReadSessionDep,
    current_user: CurrentReadUserDep,
) -> TaskDetailsResponse:
    """получить детальную информацию по задаче пользователя"""
    item = get_user_task_details(
        session,
        user_id=current_user.id,
        task_id=task_id,
    )
    return TaskDetailsResponse.from_item(item)


@router.get("/{task_id}/result", response_model=TaskResultResponse)
def get_task_result(
    task_id: UUID,
    session: ReadSessionDep,
    current_user: CurrentReadUserDep,
) -> TaskResultResponse:
    """получить задачу пользователя вместе с результатом обработки"""
    bundle = get_user_task_result(
        session,
        user_id=current_user.id,
        task_id=task_id,
    )
    return TaskResultResponse.from_bundle(bundle)