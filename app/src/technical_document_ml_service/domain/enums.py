"""перечисления, используемые в доменной модели сервиса"""

from enum import Enum


class UserRole(str, Enum):
    """роли пользователей в системе"""

    USER = "user"
    ADMIN = "admin"


class TaskStatus(str, Enum):
    """статусы жизненного цикла ML-задачи"""

    CREATED = "created"
    QUEUED = "queued"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TransactionType(str, Enum):
    """типы транзакций по балансу пользователя"""

    CREDIT = "credit"
    DEBIT = "debit"


class DocumentType(str, Enum):
    """типы документов предметной области"""

    TECHNICAL_PASSPORT = "technical_passport"
    QUALITY_PASSPORT = "quality_passport"
    LAB_PROTOCOL = "lab_protocol"
    CERTIFICATE = "certificate"
    UNKNOWN = "unknown"