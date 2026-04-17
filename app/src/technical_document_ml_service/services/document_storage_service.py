from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from uuid import UUID, uuid4

from technical_document_ml_service.core.config import app_settings


@dataclass(frozen=True, slots=True)
class IncomingDocumentData:
    """входные данные загружаемого документа"""

    filename: str
    content_type: str | None
    content: bytes


@dataclass(frozen=True, slots=True)
class StoredDocumentData:
    """метаданные документа после сохранения в файловое хранилище"""

    original_filename: str
    storage_path: str
    mime_type: str
    size_bytes: int


def _normalize_filename(filename: str | None) -> str:
    """нормализовать имя файла"""
    if not filename:
        return "document"
    return Path(filename).name or "document"


def save_documents(
    *,
    owner_id: UUID,
    documents: list[IncomingDocumentData],
) -> list[StoredDocumentData]:
    """сохранить документы пользователя в локальное файловое хранилище"""
    base_dir = Path(app_settings.uploads_dir) / str(owner_id)
    base_dir.mkdir(parents=True, exist_ok=True)

    stored_documents: list[StoredDocumentData] = []

    for document in documents:
        original_filename = _normalize_filename(document.filename)
        suffix = Path(original_filename).suffix
        stored_filename = f"{uuid4().hex}{suffix}"
        destination = base_dir / stored_filename

        destination.write_bytes(document.content)

        stored_documents.append(
            StoredDocumentData(
                original_filename=original_filename,
                storage_path=str(destination),
                mime_type=document.content_type or "application/octet-stream",
                size_bytes=len(document.content),
            )
        )

    return stored_documents


def delete_stored_files(paths: Iterable[str]) -> None:
    """удалить ранее сохраненные файлы"""
    for path_str in paths:
        path = Path(path_str)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            continue