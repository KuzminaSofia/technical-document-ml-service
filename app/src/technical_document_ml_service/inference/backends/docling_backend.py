from __future__ import annotations

from technical_document_ml_service.inference.backends.base import PredictionBackend
from technical_document_ml_service.inference.contracts import BackendRequest, BackendResult


class DoclingBackend(PredictionBackend):
    """backend обработки на основе Docling
    воспроизводит прежнее mock-поведение сервиса
    """

    backend_name = "docling"

    def process(self, request: BackendRequest) -> BackendResult:
        """выполнить обработку через Docling stub"""
        extracted_data = {
            document.original_filename: {
                "document_type": document.document_type,
                "target_schema": request.target_schema,
                "status": "processed",
                "backend": self.name,
            }
            for document in request.documents
        }

        return BackendResult(
            extracted_data=extracted_data,
            output_path=None,
            artifacts=[],
            raw_payload={},
            warnings=[],
            metadata={
                "backend": self.name,
                "mode": "stub",
                "documents_count": len(request.documents),
            },
        )


def create_docling_backend(
    config: dict | None = None,
) -> PredictionBackend:
    """фабрика backend-а Docling"""
    return DoclingBackend(config=config)