"""исключения ML-сервиса"""


class DomainError(Exception):
    """базовое исключение доменного слоя"""


class InsufficientBalanceError(DomainError):
    """ошибка, возникающая при недостаточном балансе пользователя"""


class InvalidAmountError(DomainError):
    """ошибка, возникающая при некорректной сумме транзакции"""


class TaskExecutionError(DomainError):
    """ошибка выполнения ML-задачи"""


class ModelUnavailableError(DomainError):
    """ошибка, возникающая при обращении к недоступной ML-модели"""