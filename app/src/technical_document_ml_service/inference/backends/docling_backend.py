from __future__ import annotations

from typing import Any

from technical_document_ml_service.inference.backends.base import PredictionBackend
from technical_document_ml_service.inference.contracts import BackendRequest, BackendResult
from technical_document_ml_service.inference.exceptions import BackendExecutionError


class DoclingBackend(PredictionBackend):
    """backend обработки на основе Docling"""

    backend_name = "docling"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config=config)

    def process(self, request: BackendRequest) -> BackendResult:
        """выполнить обработку через Docling"""
        raise BackendExecutionError(
            "Backend 'docling' пока не реализован "
        )


def create_docling_backend(
    config: dict[str, Any] | None = None,
) -> PredictionBackend:
    """фабрика backend-а Docling"""
    return DoclingBackend(config=config)