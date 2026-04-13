from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _get_bool_env(name: str, default: bool) -> bool:
    """прочитать булево значение из env"""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class AppSettings:
    """основные настройки приложения"""

    storage_dir: str

    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_user: str
    rabbitmq_password: str
    rabbitmq_virtual_host: str
    rabbitmq_queue_name: str
    rabbitmq_heartbeat: int
    rabbitmq_blocked_connection_timeout: int
    rabbitmq_prefetch_count: int
    rabbitmq_ssl_enabled: bool


def load_app_settings() -> AppSettings:
    """загрузить настройки приложения из переменных окружения"""
    default_storage_dir = Path("storage/uploads")

    return AppSettings(
        storage_dir=os.getenv("APP_STORAGE_DIR", str(default_storage_dir)),
        rabbitmq_host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
        rabbitmq_port=int(os.getenv("RABBITMQ_PORT", "5672")),
        rabbitmq_user=os.getenv("RABBITMQ_USER", "guest"),
        rabbitmq_password=os.getenv("RABBITMQ_PASSWORD", "guest"),
        rabbitmq_virtual_host=os.getenv("RABBITMQ_VHOST", "/"),
        rabbitmq_queue_name=os.getenv(
            "RABBITMQ_PREDICTION_QUEUE",
            "technical_document_prediction_tasks",
        ),
        rabbitmq_heartbeat=int(os.getenv("RABBITMQ_HEARTBEAT", "60")),
        rabbitmq_blocked_connection_timeout=int(
            os.getenv("RABBITMQ_BLOCKED_CONNECTION_TIMEOUT", "30")
        ),
        rabbitmq_prefetch_count=int(os.getenv("RABBITMQ_PREFETCH_COUNT", "1")),
        rabbitmq_ssl_enabled=_get_bool_env("RABBITMQ_SSL_ENABLED", False),
    )


app_settings = load_app_settings()