from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from technical_document_ml_service.inference.contracts import BackendRequest, BackendResult


class PredictionBackend(ABC):
    """базовый интерфейс backend-обработчика"""

    backend_name: ClassVar[str]

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config: dict[str, Any] = dict(config or {})

    @property
    def name(self) -> str:
        """вернуть системное имя backend"""
        return self.backend_name

    @property
    def config(self) -> dict[str, Any]:
        """вернуть конфигурацию backend"""
        return dict(self._config)

    @abstractmethod
    def process(self, request: BackendRequest) -> BackendResult:
        """выполнить обработку запроса"""
        raise NotImplementedError