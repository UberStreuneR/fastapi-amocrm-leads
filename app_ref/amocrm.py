from typing import Callable, Union, List
import aiohttp
import asyncio
import requests
from settings_ import settings
from datetime import datetime, timedelta


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
        self._account = account
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_url = redirect_url
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._auth_code = auth_code
        self._on_auth = on_auth
        #self._success_stage_id = None
        #self._pipeline_id = None

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
                          self._refresh_token)

    def _make_request(
        self, method: str, path: str, data: Union[dict, List[dict]] = None, is_auth: bool = False
    ) -> dict:
        """Сделать запрос к API amoCRM"""

        kwargs = {"headers": {"authorization": f"Bearer {self._access_token}"}}

        if method.lower() == "get":
            kwargs["params"] = data
        else:
            kwargs["json"] = data

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

    # TODO: Delete when not needed anymore
    def _make_test_request(self):
        return self._make_request("get", "/api/v4/leads")

    def get_contact_leads(self, contact_id: str):
        data = {"with": "leads"}
        response = self._make_request(
            "get", f"/api/v4/contacts/{contact_id}", data)
        return response['_embedded']['leads']

    def get_company_leads(self, company_id: str):
        data = {"with": "leads"}
        response = self._make_request(
            "get", f"/api/v4/companies/{company_id}", data)
        return response['_embedded']['leads']

    #TODO: lead_path = '/api/v4/leads/lead_id'
    def get_lead(self, lead_path: str):
        return self._make_request("get", lead_path)

    def check_lead_younger_than(self, lead: dict, months: int):
        created_at = lead['created_at']
        date = datetime.fromtimestamp(created_at)
        if datetime.now() - date > timedelta(days=int(months)*30):
            return False
        return True

    # TODO
    def prepare_pipeline_id():
        pass

    def prepare_success_stage_id():
        pass

    def check_lead_is_in_success_stage(self, lead: dict):
        if lead['status_id'] == self._success_stage_id and lead['pipeline_id'] == self._pipeline_id:
            return True
        return False

    def get_company_success_leads(self, company_id: str, months: int):
        leads = self.get_company_leads(company_id)
        success_leads = []
        for lead in leads:
            # TODO: convert it to lead_path
            lead_path = lead['_links']['self']['href']
            lead_data = self.get_lead(lead_path)
            if self.check_lead_is_in_success_stage(lead_data) and self.check_lead_younger_than(lead_data, months):
                success_leads.append(lead_data['price'])
        return success_leads

    def get_contact_success_leads(self, contact_id: str, months: int):
        leads = self.get_contact_leads(contact_id)
        success_leads = []
        for lead in leads:
            # TODO: convert it to lead_path
            lead_path = lead['_links']['self']['href']
            lead_data = self.get_lead(lead_path)
            if self.check_lead_is_in_success_stage(lead_data) and self.check_lead_younger_than(lead_data, months):
                success_leads.append(lead_data['price'])
        return success_leads

    # TODO
    def get_many_contacts(self):
        pass

    def run_contact_check(self):
        pass

    def get_value_and_label_from_list(self, items: List):
        result = []
        for item in items:
            id_and_name = {"value": str(item['id']), "label": item['name']}
            result.append(id_and_name)
        return result

    def get_company_custom_fields(self):
        response = self._make_request(
            "get", f"/api/v4/companies/custom_fields")
        fields = response['_embedded']['custom_fields']
        return self.get_value_and_label_from_list(fields)

    def get_contact_custom_fields(self):
        response = self._make_request(
            "get", f"/api/v4/contacts/custom_fields")
        fields = response['_embedded']['custom_fields']
        return self.get_value_and_label_from_list(fields)

    def get_lead_custom_fields(self):
        response = self._make_request(
            "get", f"/api/v4/leads/custom_fields")
        fields = response['_embedded']['custom_fields']
        return self.get_value_and_label_from_list(fields)

    def get_custom_fields(self):
        data = {
            "companyFields": self.get_company_custom_fields(),
            "contactFields": self.get_contact_custom_fields(),
            "leadFields": self.get_lead_custom_fields()
        }
        return data
