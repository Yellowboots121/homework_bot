class DataTypeError(Exception):
    """Ошибка, если тип данных не dict."""

    pass


class MessageSendingError(Exception):
    """Ошибка отправки сообщения."""

    pass


class FailedRequestError(Exception):
    """Ошибка запроса API."""

    pass


class EmptyError(Exception):
    """Ответ API пуст."""

    pass


class NoKeyError(Exception):
    """Отсутствует ключ."""

    pass
