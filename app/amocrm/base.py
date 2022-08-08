from .exceptions import (UnexpectedResponseCustomException,
                         BadResponseCustomException,
                         NotAuthorizedCustomException)
from app.app_settings import settings
import requests
import time


from typing import Callable, Union, List, Generator

import logging
import sys
logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("Sockets")
logging.getLogger("chardet.charsetprober").disabled = True


class AmoCRM:
    """Базовый класс для работы с AmoCRM API"""

    def __init__(
        self,
        account: str,
        client_id: str,
        client_secret: str,
        redirect_url: str = None,
        access_token: str = None,
        refresh_token: str = None,
        auth_code: str = None,
        on_auth: Callable = None,
    ):
        self._account = account
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_url = redirect_url
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._auth_code = auth_code
        self._on_auth = on_auth

    @property
    def url(self) -> str:
        """Адрес crm системы компании"""
        return f"https://{self._account}.amocrm.ru"

    @property
    def client_id(self) -> str:
        """client_id интеграции"""
        return self._client_id

    def authorize(self, grant_type: str, token: str) -> dict:
        """
        Пройти авторизацию с указанным grant_type,
        поддерживаются refresh_token и authorization_code
        """

        if grant_type == "refresh_token":
            token_field = grant_type
        elif grant_type == "authorization_code":
            token_field = "code"
        else:
            raise ValueError(f"Invalid grant type `grant_type={grant_type}`")
        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "redirect_uri": self._redirect_url or self.url,
            "grant_type": grant_type,
            token_field: token,
        }
        result = self.make_request(
            "post", "oauth2/access_token", data, is_auth=True)

        self._access_token = result["access_token"]
        self._refresh_token = result["refresh_token"]

        if self._on_auth is not None:
            self._on_auth(self._client_id, self._access_token,
                          self._refresh_token, instance=self)

    def make_request(
        self, method: str, path: str, data: Union[dict, List[dict]] = None, is_auth: bool = False
    ) -> dict:
        """Сделать запрос к API amoCRM"""

        kwargs = {"headers": {"authorization": f"Bearer {self._access_token}"}}

        if method.lower() == "get":
            kwargs["params"] = data
        elif method.lower() == "post":
            kwargs["json"] = data
        else:
            kwargs["data"] = data

        response = requests.request(method, f"{self.url}/{path}", **kwargs)
        if not is_auth and response.status_code == 401:
            # Если вернулся код 401 и этот запрос не связан с авторизацией, то мы
            # поочередно пробуем авторизоваться через refresh_token и authorization_code
            try:
                self.authorize("refresh_token", self._refresh_token)
            except UnexpectedResponseCustomException:
                self.authorize("authorization_code", self._auth_code)

            return self.make_request(method, path, data)

        if response.status_code == 401:
            raise NotAuthorizedCustomException(response)
        elif response.status_code == 400:
            raise BadResponseCustomException
        elif response.status_code >= 300:
            raise UnexpectedResponseCustomException
        logger.info(f"Response: {response.status_code} {response.json()}")
        return response.json()

    def get_many(
        self, entity: str, path: str, params: dict = None, limit: int = 50
    ) -> Generator[dict, None, None]:
        """Получить все сущности в виде генератора"""

        if params is None:
            params = {}

        params.update({"page": 1, "limit": limit})

        while True:
            result = self.make_request("get", path, params)
            # Сервер может вернуть 204 код, при определенных фильтрах, это означает,
            # что сущностей подходящих под этот фильтр не найдено
            if result.status_code == 204:
                break

            yield from result["_embedded"][entity]
            if "next" not in result["_links"]:
                break
            time.sleep(10)  # лимит в 50 сущностей -> 5 сущностей в секунду

            params["page"] += 1

    def create_hook(self) -> Union[dict, None]:
        """Создать хук на изменение сделки"""

        webhook_endpoint = settings.app_host + "settings/handle-hook"

        webhook_post_data = {
            "destination": webhook_endpoint,
            "settings": ["restore_lead", "add_lead", "status_lead"]
        }

        params = {
            "filter[destination]": webhook_endpoint
        }

        current_hooks = self.make_request(
            "get", "api/v4/webhooks", data=params)

        if webhook_endpoint not in current_hooks:
            return self.make_request("post", "api/v4/webhooks",
                                     data=webhook_post_data)

    def delete_hook(self) -> None:
        """Удалить хук на изменение сделки"""

        webhook_endpoint = settings.app_host + "settings/handle-hook"
        self.make_request("delete", "api/v4/webhooks",
                          {"destination": webhook_endpoint})
