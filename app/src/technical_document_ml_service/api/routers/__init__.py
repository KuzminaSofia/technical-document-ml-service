from technical_document_ml_service.api.routers.auth import router as auth_router
from technical_document_ml_service.api.routers.health import router as health_router
from technical_document_ml_service.api.routers.users import router as users_router

__all__ = [
    "auth_router",
    "health_router",
    "users_router",
]