from abc import abstractmethod, ABC
from app.amocrm.base import AmoCRM
from .helpers import (get_success_and_active_leads,
                      make_patch_request_data,
                      make_many_patch_request_data,
                      get_fields_from_many,
                      get_value_and_label_from_list)

import json
from typing import Generator, List


class EntityManager(ABC):
    """Базовый класс для запросов к сущностям AmoCRM"""

    def __init__(self, amocrm: AmoCRM) -> None:
        self.amocrm = amocrm

    @abstractmethod
    def get_one(self):
        """Получить одну сущность"""

        pass

    @abstractmethod
    def get_many(self):
        """Получить сущности из генератора"""

        pass

    @abstractmethod
    def get_leads(self):
        """Получить сделки для сущности (только компании и контакты)"""

        pass

    @abstractmethod
    def get_success_leads(self):
        """Получить активные сделки"""

        pass

    @abstractmethod
    def set_field(self):
        """Установить поле сущности"""

        pass

    @abstractmethod
    def set_many_fields(self):
        """Установить поля нескольких сущностей одним запросом"""

        pass

    @abstractmethod
    def get_custom_fields(self):
        """Получить кастомные поля сущности"""

        pass


class ContactManager(EntityManager):
    """Класс для запроса по контактам AmoCRM"""

    def get_one(self, contact_id: int) -> dict:
        data = {"with": "leads"}
        return self.amocrm.make_request(
            "get", f"/api/v4/contacts/{contact_id}", data)

    def get_many(self) -> Generator[dict, None, None]:
        yield from self.amocrm.get_many("contacts", "api/v4/contacts")

    def get_leads(self, contact_id: int) -> List[dict]:
        data = {"with": "leads"}
        response = self.amocrm.make_request(
            "get", f"/api/v4/contacts/{contact_id}", data)
        return response["_embedded"]["leads"]

    def get_success_leads(self, contact_id: int, months: int):
        leads = self.get_leads(contact_id)
        return get_success_and_active_leads(LeadManager(self.amocrm), months, leads)

    def set_field(self, contact_id: int, contact_field_id: int, value: int) -> dict:
        data = make_patch_request_data(contact_field_id, value)
        return self.amocrm.make_request("patch", f"api/v4/contacts/{contact_id}", json.dumps(data))

    def set_many_fields(self, entries: List[dict]) -> dict:
        return self.amocrm.make_request("patch", f"api/v4/contacts", json.dumps(entries))

    def get_custom_fields(self, field_type: str) -> List[dict]:
        generator = self.amocrm.get_many(
            "custom_fields", f"/api/v4/contacts/custom_fields")
        fields = get_fields_from_many(generator, field_type)
        return get_value_and_label_from_list(fields)


class CompanyManager(EntityManager):
    """Класс для запроса по компаниям AmoCRM"""

    def get_one(self, company_id: int) -> dict:
        data = {"with": "leads"}
        return self.amocrm.make_request(
            "get", f"/api/v4/companies/{company_id}", data)

    def get_many(self) -> Generator[dict, None, None]:
        yield from self.amocrm.get_many("companies", "api/v4/companies")

    def get_leads(self, company_id: int) -> List[dict]:
        data = {"with": "leads"}
        response = self.amocrm.make_request(
            "get", f"/api/v4/companies/{company_id}", data)
        return response["_embedded"]["leads"]

    def get_success_leads(self, company_id: int, months: int):
        leads = self.get_leads(company_id)
        return get_success_and_active_leads(LeadManager(self.amocrm), months, leads)

    def set_field(self, company_id: int, company_field_id: int, value: int) -> dict:
        data = make_patch_request_data(company_field_id, value)
        return self.amocrm.make_request("patch", f"api/v4/companies/{company_id}", json.dumps(data))

    def set_many_fields(self, entries: List[dict]) -> dict:
        return self.amocrm.make_request("patch", f"api/v4/companies", json.dumps(entries))

    def get_custom_fields(self, field_type: str) -> List[dict]:
        generator = self.amocrm.get_many(
            "custom_fields", f"/api/v4/companies/custom_fields")
        fields = get_fields_from_many(generator, field_type)
        return get_value_and_label_from_list(fields)


class LeadManager(EntityManager):
    """Класс для запроса по сделкам AmoCRM"""

    def __init__(self, amocrm: AmoCRM):
        self.amocrm = amocrm

    def get_one(self, lead_id) -> dict:
        return self.amocrm.make_request(
            "get", f"/api/v4/leads/{lead_id}", {"with": "contacts"})

    def get_custom_fields(self, field_type: str = "numeric") -> List[dict]:
        """Только поля numeric используются для сущности лид"""

        generator = self.amocrm.get_many(
            "custom_fields", f"/api/v4/leads/custom_fields")
        numeric_fields = self.get_fields_from_many(generator, field_type)
        return get_value_and_label_from_list(numeric_fields)

    def set_field(self, lead_id: int, lead_field_id: int, value: int) -> dict:
        data = make_patch_request_data(lead_field_id, value)
        return self.amocrm.make_request("patch", f"api/v4/leads/{lead_id}", json.dumps(data))

    def set_many_fields(self, entries: List[dict]) -> dict:
        data = make_many_patch_request_data(entries)
        return self.amocrm.make_request("patch", f"api/v4/leads", json.dumps(data))

    """Для сущности сделка методы ниже не нужны или не имеют смысла"""

    def get_many(self):
        pass

    def get_leads(self):
        pass

    def get_success_leads(self):
        pass


class MetaManager:
    """Объединяющий класс"""

    def __init__(self, amocrm: AmoCRM):
        self.contacts = ContactManager(amocrm)
        self.companies = CompanyManager(amocrm)
        self.leads = LeadManager(amocrm)

    def get_custom_fields(self) -> dict:
        """Получить кастомные поля для всех сущностей"""

        data = {
            "companyNumericFields": self.companies.get_custom_fields("numeric"),
            "companyStringFields": self.companies.get_custom_fields("text"),
            "contactNumericFields": self.contacts.get_custom_fields("numeric"),
            "contactStringFields": self.contacts.get_custom_fields("text"),
            "leadFields": self.leads.get_custom_fields("numeric"),
        }
        return data
