from typing import Callable, Union, List, Generator
import requests
from settings_ import settings
from datetime import datetime, timedelta
import time
import json


class UnexpectedResponse(Exception):
    """Обертка для не 200х ответов от amoCRM"""

    def __init__(self, response: requests.Response):
        self.response = response

        flatten_text = " ".join(response.text.split())
        message = f"Unexpected response `status_code={response.status_code}` `text={flatten_text}`"

        super().__init__(message)


class AmoCRM:
    """Клиент для работы с API amoCRM"""

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
        # Note: type code, could possibly be replaced with a schema
        # def __init__(integrationProps) -> ...
        self._account = account
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_url = redirect_url
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._auth_code = auth_code
        self._on_auth = on_auth

    def _set_pipeline_id(self):
        if settings.pipeline_id is None:
            response = self._make_request("get", "api/v4/leads/pipelines")
            for pipeline in response['_embedded']['pipelines']:
                if pipeline['name'] == "Продажа":
                    settings.pipeline_id = pipeline['id']
                    break

    def _set_success_stage_id(self):
        if settings.success_stage_id is None:
            response = self._make_request(
                "get", f"api/v4/leads/pipelines/{settings.pipeline_id}")
            for status in response['_embedded']['statuses']:
                if status['name'] == 'Закрыто. Оплата получена':
                    settings.success_stage_id = status['id']
                    break

    def _set_inactive_stage_ids(self):
        inactive_statuses = []
        if settings.inactive_stage_ids is None:
            response = self._make_request("get", "api/v4/leads/pipelines")
            for pipeline in response['_embedded']['pipelines']:
                for status in pipeline['_embedded']['statuses']:
                    if not status['is_editable']:
                        inactive_statuses.append(status['id'])
        settings.inactive_stage_ids = inactive_statuses
        print(settings.inactive_stage_ids)

    @property
    def url(self) -> str:
        """Адрес crm системы компании"""
        return f"https://{self._account}.amocrm.ru"

    @property
    def client_id(self):
        """client_id интеграции"""
        return self._client_id

    def authorize(self, grant_type: str, token: str):
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

        result = self._make_request(
            "post", "oauth2/access_token", data, is_auth=True)

        self._access_token = result["access_token"]
        self._refresh_token = result["refresh_token"]

        if self._on_auth is not None:
            self._on_auth(self._client_id, self._access_token,
                          self._refresh_token, instance=self)

    def _make_request(
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
            except UnexpectedResponse:
                self.authorize("authorization_code", self._auth_code)

            return self._make_request(method, path, data)

        if response.status_code != 200:
            raise UnexpectedResponse(response)

        return response.json()

    def get_contact_leads(self, contact_id: str):
        data = {"with": "leads"}
        response = self._make_request(
            "get", f"/api/v4/contacts/{contact_id}", data)
        return response['_embedded']['leads']

    def get_company_leads(self, company_id: str):
        data = {"with": "leads"}
        response = self._make_request(
            "get", f"/api/v4/companies/{company_id}", data)
        # print(f"COMPANY RESPONSE {response['_embedded']['leads']}\n\n\n")
        return response['_embedded']['leads']

    def get_lead(self, lead_path: str):
        return self._make_request("get", lead_path)

    # 'https://devks.amocrm.ru/api/v4/leads/35178445... -> 'api/v4/leads/35178445'
    def get_lead_path(self, string):
        return string[string.find("api"):string.find("?")]

    def check_lead_younger_than(self, lead: dict, months: int):
        created_at = lead['created_at']
        date = datetime.fromtimestamp(created_at)
        if datetime.now() - date > timedelta(days=int(months)*30):
            return False
        return True

    def check_lead_is_in_success_stage(self, lead: dict):
        if settings.pipeline_id is None:
            self._set_pipeline_id()
        if settings.success_stage_id is None:
            self._set_success_stage_id()

        if lead['status_id'] == settings.success_stage_id and lead['pipeline_id'] == settings.pipeline_id:
            return True
        return False

    def check_lead_is_active(self, lead: dict):
        if settings.inactive_stage_ids is None:
            self._set_inactive_stage_ids()
        if lead['status_id'] not in settings.inactive_stage_ids:
            return True
        return False

    def get_success_and_active_leads(self, months, leads):
        success_leads = []
        active_leads = []
        for lead in leads:
            lead_path = self.get_lead_path(lead['_links']['self']['href'])
            lead_data = self.get_lead(lead_path)
            if self.check_lead_is_in_success_stage(lead_data) and self.check_lead_younger_than(lead_data, months):
                success_leads.append(lead_data['price'])
            elif self.check_lead_is_active(lead_data):
                active_leads.append(lead_data['id'])
        return success_leads, active_leads

    def get_company_success_leads(self, company_id: str, months: int):
        leads = self.get_company_leads(company_id)
        return self.get_success_and_active_leads(months, leads)

    def get_contact_success_leads(self, contact_id: str, months: int):
        leads = self.get_contact_leads(contact_id)
        return self.get_success_and_active_leads(months, leads)

    def _make_patch_request_data(self, field_id, value):
        data = {
            "custom_fields_values": [{
                'field_id': field_id,
                'values': [
                    {
                        "value": value
                    }
                ]
            }]
        }

        return data

    def set_company_field(self, company_id: int, company_field_id: int, value: int):
        # print(type(company_id), type(company_field_id), type(value))
        data = self._make_patch_request_data(company_field_id, value)
        return self._make_request("patch", f"api/v4/companies/{company_id}", json.dumps(data))

    def set_contact_field(self, contact_id: int, contact_field_id: int, value: int):
        print(type(contact_id), type(contact_field_id), type(value))
        data = self._make_patch_request_data(contact_field_id, value)
        return self._make_request("patch", f"api/v4/contacts/{contact_id}", json.dumps(data))

    def set_lead_field(self, lead_id: int, lead_field_id: int, value: int):
        # print(type(lead_id), type(lead_field_id), type(value))
        assert type(lead_field_id) == int
        data = self._make_patch_request_data(lead_field_id, value)
        return self._make_request("patch", f"api/v4/leads/{lead_id}", json.dumps(data))

    def _get_many(
        self, entity: str, path: str, params: dict = None, limit: int = 50
    ) -> Generator[dict, None, None]:
        """Получить все сущности в виде генератора"""

        if params is None:
            params = {}

        params.update({"page": 1, "limit": limit})

        while True:
            try:
                result = self._make_request("get", path, params)
            except UnexpectedResponse as e:
                # Сервер может вернуть 204 код, при определенных фильтрах, это означает,
                # что сущностей подходящих под этот фильтр не найдено
                if e.response.status_code == 204:
                    break
                raise

            yield from result["_embedded"][entity]
            if "next" not in result["_links"]:
                break
            time.sleep(10)  # limit of 50 -> 5 entities per second

            params["page"] += 1

    def get_many_contacts(self):
        yield from self._get_many("contacts", "api/v4/contacts")

    def get_many_companies(self):
        yield from self._get_many("companies", "api/v4/companies")

    def get_value_and_label_from_list(self, items: List):
        result = []
        for item in items:
            id_and_name = {"value": str(item['id']), "label": item['name']}
            result.append(id_and_name)
        return result

    def get_fields_from_many(self, fields: Generator, field_type: str):
        numeric_fields = [
            field for field in fields if field['type'] == field_type]
        return numeric_fields

    def get_company_custom_fields(self, field_type: str):
        generator = self._get_many(
            "custom_fields", f"/api/v4/companies/custom_fields")
        fields = self.get_fields_from_many(generator, field_type)
        return self.get_value_and_label_from_list(fields)

    def get_contact_custom_fields(self, field_type: str):
        generator = self._get_many(
            "custom_fields", f"/api/v4/contacts/custom_fields")
        fields = self.get_fields_from_many(generator, field_type)
        return self.get_value_and_label_from_list(fields)

    def get_lead_custom_fields(self, field_type: str = "numeric"):
        """Only numeric fields are used for entity type lead"""
        generator = self._get_many(
            "custom_fields", f"/api/v4/leads/custom_fields")
        numeric_fields = self.get_fields_from_many(generator, field_type)
        return self.get_value_and_label_from_list(numeric_fields)

    def get_custom_fields(self):
        data = {
            "companyNumericFields": self.get_company_custom_fields("numeric"),
            "companyStringFields": self.get_company_custom_fields("text"),
            "contactNumericFields": self.get_contact_custom_fields("numeric"),
            "contactStringFields": self.get_contact_custom_fields("text"),
            "leadFields": self.get_lead_custom_fields("numeric"),
        }
        return data
