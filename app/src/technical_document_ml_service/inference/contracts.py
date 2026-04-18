from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BackendDocument:
    """описание документа, передаваемого в backend обработки"""

    document_id: UUID
    owner_id: UUID
    original_filename: str
    storage_path: str
    mime_type: str
    document_type: str
    size_bytes: int

    @property
    def path(self) -> Path:
        """вернуть путь к файлу в виде Path"""
        return Path(self.storage_path)


@dataclass(frozen=True, slots=True)
class BackendArtifact:
    """описание одного сохраненного артефакта backend-обработки"""

    name: str
    path: str
    kind: str
    mime_type: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_manifest_entry(self) -> dict[str, Any]:
        """преобразовать артефакт в JSON-совместимую запись"""
        return {
            "name": self.name,
            "path": self.path,
            "kind": self.kind,
            "mime_type": self.mime_type,
            "description": self.description,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class BackendRequest:
    """унифицированный запрос к backend обработки"""

    task_id: UUID
    user_id: UUID
    model_id: UUID
    model_name: str
    model_kind: str
    backend_name: str
    backend_config: dict[str, Any]
    target_schema: str
    documents: list[BackendDocument]
    artifacts_dir: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BackendResult:
    """унифицированный результат работы backend"""

    extracted_data: dict[str, Any] = field(default_factory=dict)
    output_path: str | None = None
    artifacts: list[BackendArtifact] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def build_artifacts_manifest(self) -> list[dict[str, Any]]:
        """собрать сериализуемый manifest артефактов"""
        return [artifact.to_manifest_entry() for artifact in self.artifacts]