from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PredictionTaskMessage:
    """
    сообщение о постановке ML-зачи в очередь
    тяжелые данные хранятся в БД и storage
    """

    task_id: UUID
    user_id: UUID
    model_name: str
    timestamp: datetime
    version: int = 1

    def to_payload(self) -> dict[str, str | int]:
        """преобразовать сообщение в сериализуемый словарь"""
        return {
            "version": self.version,
            "task_id": str(self.task_id),
            "user_id": str(self.user_id),
            "model_name": self.model_name,
            "timestamp": self.timestamp.astimezone(UTC).isoformat(),
        }

    def to_json(self) -> str:
        """сериализовать сообщение в JSON-строку"""
        return json.dumps(
            self.to_payload(),
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def to_bytes(self) -> bytes:
        """сериализовать сообщение в байты для отправки в RabbitMQ"""
        return self.to_json().encode("utf-8")

    @classmethod
    def from_payload(cls, payload: dict[str, str | int]) -> "PredictionTaskMessage":
        """создать сообщение из словаря"""
        return cls(
            version=int(payload["version"]),
            task_id=UUID(str(payload["task_id"])),
            user_id=UUID(str(payload["user_id"])),
            model_name=str(payload["model_name"]),
            timestamp=datetime.fromisoformat(str(payload["timestamp"])),
        )

    @classmethod
    def from_json(cls, raw_json: str) -> "PredictionTaskMessage":
        """создать сообщение из JSON-строки"""
        payload = json.loads(raw_json)
        if not isinstance(payload, dict):
            raise ValueError("Некорректный формат сообщения очереди.")
        return cls.from_payload(payload)

    @classmethod
    def from_bytes(cls, raw_bytes: bytes) -> "PredictionTaskMessage":
        """создать сообщение из байтового представления"""
        return cls.from_json(raw_bytes.decode("utf-8"))