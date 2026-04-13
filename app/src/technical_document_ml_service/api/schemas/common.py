from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorInfo(BaseModel):
    """описание ошибки API"""

    code: str = Field(description="машинно-читаемый код ошибки")
    message: str = Field(description="человеко-читаемое описание ошибки")
    details: Any | None = Field(default=None, description="дополнительные детали")


class ErrorResponse(BaseModel):
    """единый формат ошибки API"""

    error: ErrorInfo


class HealthResponse(BaseModel):
    """ответ health-check эндпоинта"""

    status: str