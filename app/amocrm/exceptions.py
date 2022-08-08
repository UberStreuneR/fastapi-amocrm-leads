from requests import Response


class BaseResponseCustomException(Exception):
    """Базовый класс для исключений """

    def __init__(self, response: Response):
        self.response = response
        self.url = response.url
        self.status_code = response.status_code
        self.text = response.text
        super().__init__()


class UnexpectedResponseCustomException(BaseResponseCustomException):
    """Класс исключение для не 2xx ответов от amoCRM"""

    def __init__(self, response: Response):
        super().__init__(response)

    def __str__(self):
        return f'Unexpected response: {self.url} - {self.status_code} - {self.text}'


class NotAuthorizedCustomException(BaseResponseCustomException):
    """Класс исключение для ответа 401 от amoCRM"""

    def __init__(self, response: Response):
        super().__init__(response)

    def __str__(self):
        return f'NotAuthorized response: {self.url} - {self.status_code} - {self.text}'


class BadResponseCustomException(BaseResponseCustomException):
    """Класс исключение для ответа 400 от amoCRM"""

    def __init__(self, response: Response):
        super().__init__(response)

    def __str__(self):
        return f'Bad response: {self.url} - {self.status_code} - {self.text}'
