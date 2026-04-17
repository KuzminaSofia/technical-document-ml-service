from __future__ import annotations

from uuid import uuid4

from technical_document_ml_service.inference.backends.docling_backend import (
    DoclingBackend,
)
from technical_document_ml_service.inference.contracts import (
    BackendDocument,
    BackendRequest,
)


def test_docling_backend_generates_stub_artifacts_when_docling_unavailable(
    monkeypatch,
    tmp_path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test content")

    def _raise_module_not_found():
        raise ModuleNotFoundError("docling is not installed")

    monkeypatch.setattr(
        "technical_document_ml_service.inference.backends.docling_backend._load_document_converter_cls",
        _raise_module_not_found,
    )

    backend = DoclingBackend()

    request = BackendRequest(
        task_id=uuid4(),
        user_id=uuid4(),
        model_id=uuid4(),
        model_name="technical-document-extractor-basic",
        model_kind="technical_document_extraction",
        backend_name="docling",
        backend_config={},
        target_schema="passport_fields",
        documents=[
            BackendDocument(
                document_id=uuid4(),
                owner_id=uuid4(),
                original_filename="sample.pdf",
                storage_path=str(pdf_path),
                mime_type="application/pdf",
                document_type="unknown",
                size_bytes=pdf_path.stat().st_size,
            )
        ],
        artifacts_dir=str(tmp_path / "artifacts"),
        context={},
    )

    result = backend.process(request)

    assert result.output_path is not None
    assert len(result.artifacts) == 5
    assert "sample.pdf" in result.extracted_data
    assert result.extracted_data["sample.pdf"]["backend"] == "docling"
    assert result.extracted_data["sample.pdf"]["status"] == "processed"
    assert result.extracted_data["sample.pdf"]["mode"] == "stub_fallback"
    assert len(result.warnings) == 1