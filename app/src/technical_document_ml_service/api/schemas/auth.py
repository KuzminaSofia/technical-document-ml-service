from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from technical_document_ml_service.api.schemas.users import UserResponse


class _AuthCredentialsBase(BaseModel):
    """базовая схема учетных данных пользователя"""

    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("Некорректный email.")
        return normalized


class RegisterRequest(_AuthCredentialsBase):
    """тело запроса на регистрацию"""


class LoginRequest(_AuthCredentialsBase):
    """тело запроса на авторизацию"""


class AuthResponse(BaseModel):
    """ответ успешной регистрации / авторизации"""

    message: str
    user: UserResponse