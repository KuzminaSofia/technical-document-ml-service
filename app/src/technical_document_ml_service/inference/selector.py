from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from technical_document_ml_service.core.config import app_settings
from technical_document_ml_service.inference.backends.base import PredictionBackend
from technical_document_ml_service.inference.registry import (
    DEFAULT_BACKEND_REGISTRY,
    BackendRegistry,
)


@dataclass(frozen=True, slots=True)
class BackendSelection:
    """результат выбора backend-а обработки"""

    requested_backend_name: str | None
    resolved_backend_name: str
    backend: PredictionBackend


def select_prediction_backend(
    *,
    requested_backend_name: str | None,
    backend_config: dict[str, Any] | None = None,
    registry: BackendRegistry | None = None,
    default_backend_name: str | None = None,
) -> BackendSelection:
    """
    выбрать backend обработки

    Приоритет:
    1. backend, явно заданный у модели;
    2. backend по умолчанию из параметра;
    3. backend по умолчанию из конфигурации приложения
    """
    effective_registry = registry or DEFAULT_BACKEND_REGISTRY
    fallback_backend_name = default_backend_name or app_settings.default_prediction_backend

    resolved_backend_name = (
        requested_backend_name.strip().lower()
        if requested_backend_name and requested_backend_name.strip()
        else fallback_backend_name.strip().lower()
    )

    backend = effective_registry.create(
        name=resolved_backend_name,
        config=backend_config,
    )

    return BackendSelection(
        requested_backend_name=requested_backend_name,
        resolved_backend_name=resolved_backend_name,
        backend=backend,
    )