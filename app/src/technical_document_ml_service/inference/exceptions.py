from __future__ import annotations


class InferenceError(Exception):
    """базовая ошибка inference-слоя"""


class BackendNotFoundError(InferenceError):
    """запрошенный backend не зарегистрирован"""


class InvalidBackendConfigurationError(InferenceError):
    """передана некорректная конфигурация backend"""


class BackendExecutionError(InferenceError):
    """ошибка во время выполнения backend"""