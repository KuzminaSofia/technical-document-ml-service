from __future__ import annotations

import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any

from technical_document_ml_service.inference.backends.base import PredictionBackend
from technical_document_ml_service.inference.contracts import (
    BackendArtifact,
    BackendRequest,
    BackendResult,
)
from technical_document_ml_service.inference.exceptions import BackendExecutionError


LOGGER = logging.getLogger("technical_document_ml_service.docling_backend")


def _load_document_converter_cls():
    """лениво загрузить DocumentConverter, чтобы app-контейнер не требовал docling"""
    from docling.document_converter import DocumentConverter

    return DocumentConverter


def _to_jsonable(obj: Any):
    """преобразовать произвольный объект в JSON-сериализуемый вид"""
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_jsonable(x) for x in obj]
    if callable(obj):
        return f"<callable:{getattr(obj, '__name__', type(obj).__name__)}>"
    return str(obj)


def _save_json(path: Path, data: Any) -> None:
    """сохранить данные в JSON-файл"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_to_jsonable(data), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _sanitize_stem(filename: str) -> str:
    """безопасно нормализовать stem имени файла для каталога/артефактов"""
    raw_stem = Path(filename).stem or "document"
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", raw_stem).strip("._")
    return normalized or "document"


class DoclingBackend(PredictionBackend):
    """backend обработки на основе Docling"""

    backend_name = "docling"

    def _is_stub_fallback_allowed(self) -> bool:
        """разрешен ли явный fallback на stub-режим"""
        return bool(self.config.get("allow_stub_fallback", False))

    def process(self, request: BackendRequest) -> BackendResult:
        """выполнить обработку через Docling"""
        task_artifacts_dir = Path(request.artifacts_dir)
        task_artifacts_dir.mkdir(parents=True, exist_ok=True)

        artifacts: list[BackendArtifact] = []
        extracted_data: dict[str, Any] = {}
        warnings: list[str] = []
        documents_summary: list[dict[str, Any]] = []

        try:
            mode = "docling"
            try:
                converter_cls = _load_document_converter_cls()
                converter = converter_cls()
            except ModuleNotFoundError as exc:
                if not self._is_stub_fallback_allowed():
                    raise BackendExecutionError(
                        "Пакет 'docling' недоступен в текущем окружении. "
                        "Stub fallback отключен."
                    ) from exc

                converter = None
                mode = "stub_fallback"
                warning_message = (
                    "Пакет docling недоступен в текущем окружении. "
                    "Использован разрешенный stub fallback."
                )
                warnings.append(warning_message)
                LOGGER.warning(
                    "task_id=%s | backend=%s | %s",
                    request.task_id,
                    self.name,
                    warning_message,
                )

            for index, document in enumerate(request.documents, start=1):
                safe_stem = _sanitize_stem(document.original_filename)
                doc_dir = (
                    task_artifacts_dir
                    / f"{index:02d}_{safe_stem}_{str(document.document_id)[:8]}"
                )
                doc_dir.mkdir(parents=True, exist_ok=True)

                json_path = doc_dir / f"{safe_stem}.docling.json"
                md_path = doc_dir / f"{safe_stem}.docling.md"
                txt_path = doc_dir / f"{safe_stem}.docling.txt"
                summary_path = doc_dir / f"{safe_stem}.summary.json"

                try:
                    if converter is not None:
                        result = converter.convert(str(document.path))
                        parsed_document = result.document

                        doc_json = parsed_document.export_to_dict()
                        markdown = parsed_document.export_to_markdown()
                        text = parsed_document.export_to_text()
                        current_mode = "docling"
                    else:
                        doc_json = {
                            "source_file": str(document.path),
                            "original_filename": document.original_filename,
                            "mime_type": document.mime_type,
                            "document_type": document.document_type,
                            "backend": self.name,
                            "mode": "stub_fallback",
                            "status": "processed",
                        }
                        markdown = (
                            f"# {document.original_filename}\n\n"
                            "Docling недоступен в текущем окружении. "
                            "Сформирован stub-результат."
                        )
                        text = (
                            f"Document: {document.original_filename}\n"
                            f"Backend: {self.name}\n"
                            "Mode: stub_fallback\n"
                            "Docling package is unavailable in this environment.\n"
                        )
                        current_mode = "stub_fallback"

                    _save_json(json_path, doc_json)
                    md_path.write_text(markdown, encoding="utf-8")
                    txt_path.write_text(text, encoding="utf-8")

                    document_summary = {
                        "document_id": str(document.document_id),
                        "input_file": str(document.path),
                        "original_filename": document.original_filename,
                        "json_file": str(json_path),
                        "markdown_file": str(md_path),
                        "text_file": str(txt_path),
                        "status": "success",
                        "backend": self.name,
                        "mode": current_mode,
                    }
                    _save_json(summary_path, document_summary)

                except BackendExecutionError:
                    raise
                except Exception as exc:
                    raise BackendExecutionError(
                        f"Ошибка Docling при обработке файла '{document.original_filename}': {exc}"
                    ) from exc

                artifacts.extend(
                    [
                        BackendArtifact(
                            name=json_path.name,
                            path=str(json_path),
                            kind="docling_json",
                            mime_type="application/json",
                            description="Структурированный экспорт Docling в JSON",
                            metadata={
                                "document_id": str(document.document_id),
                                "original_filename": document.original_filename,
                                "mode": current_mode,
                            },
                        ),
                        BackendArtifact(
                            name=md_path.name,
                            path=str(md_path),
                            kind="markdown",
                            mime_type="text/markdown",
                            description="Экспорт распознанного документа в Markdown",
                            metadata={
                                "document_id": str(document.document_id),
                                "original_filename": document.original_filename,
                                "mode": current_mode,
                            },
                        ),
                        BackendArtifact(
                            name=txt_path.name,
                            path=str(txt_path),
                            kind="plain_text",
                            mime_type="text/plain",
                            description="Плоский текст документа",
                            metadata={
                                "document_id": str(document.document_id),
                                "original_filename": document.original_filename,
                                "mode": current_mode,
                            },
                        ),
                        BackendArtifact(
                            name=summary_path.name,
                            path=str(summary_path),
                            kind="document_summary",
                            mime_type="application/json",
                            description="Сводка по обработке одного документа",
                            metadata={
                                "document_id": str(document.document_id),
                                "original_filename": document.original_filename,
                                "mode": current_mode,
                            },
                        ),
                    ]
                )

                extracted_data[document.original_filename] = {
                    "document_id": str(document.document_id),
                    "document_type": document.document_type,
                    "target_schema": request.target_schema,
                    "status": "processed",
                    "backend": self.name,
                    "mode": current_mode,
                    "artifacts": {
                        "json_path": str(json_path),
                        "markdown_path": str(md_path),
                        "text_path": str(txt_path),
                        "summary_path": str(summary_path),
                    },
                }

                documents_summary.append(
                    {
                        "document_id": str(document.document_id),
                        "original_filename": document.original_filename,
                        "status": "success",
                        "mode": current_mode,
                        "summary_path": str(summary_path),
                    }
                )

            task_summary_path = task_artifacts_dir / "task.summary.json"
            task_summary = {
                "task_id": str(request.task_id),
                "user_id": str(request.user_id),
                "model_id": str(request.model_id),
                "model_name": request.model_name,
                "backend": self.name,
                "mode": mode,
                "documents_count": len(request.documents),
                "warnings": warnings,
                "documents": documents_summary,
            }
            _save_json(task_summary_path, task_summary)

            artifacts.append(
                BackendArtifact(
                    name=task_summary_path.name,
                    path=str(task_summary_path),
                    kind="task_summary",
                    mime_type="application/json",
                    description="Сводка по обработке всей задачи",
                    metadata={
                        "task_id": str(request.task_id),
                        "backend": self.name,
                        "mode": mode,
                    },
                )
            )

            return BackendResult(
                extracted_data=extracted_data,
                output_path=str(task_summary_path),
                artifacts=artifacts,
                warnings=warnings,
                metadata={
                    "backend": self.name,
                    "mode": mode,
                    "artifacts_count": len(artifacts),
                    "task_summary_path": str(task_summary_path),
                },
            )

        except Exception:
            shutil.rmtree(task_artifacts_dir, ignore_errors=True)
            raise


def create_docling_backend(
    config: dict | None = None,
) -> PredictionBackend:
    """фабрика backend-а Docling"""
    return DoclingBackend(config=config)