from __future__ import annotations

from technical_document_ml_service.web.routers.actions import router as web_actions_router
from technical_document_ml_service.web.routers.pages import router as web_pages_router

__all__ = [
    "web_pages_router",
    "web_actions_router",
]