from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv(override=False)


@dataclass(frozen=True)
class AppSettings:
    """общие настройки приложения"""

    storage_dir: str = os.getenv("APP_STORAGE_DIR", "storage/uploads")


app_settings = AppSettings()