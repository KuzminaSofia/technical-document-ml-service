from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from technical_document_ml_service.domain.entities import User
from technical_document_ml_service.domain.enums import UserRole


class UserResponse(BaseModel):
    """публичное представление пользователя"""

    id: UUID
    email: str
    role: UserRole
    balance_credits: Decimal
    is_active: bool
    created_at: datetime

    @classmethod
    def from_domain(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            role=user.role,
            balance_credits=user.balance_credits,
            is_active=user.is_active,
            created_at=user.created_at,
        )