from __future__ import annotations
from abc import ABC, abstractmethod

from fastapi import Request
from app.amocrm import AmoCRM
from sqlmodel import Session
from app.settings.schemas import CompanySetting, ContactSetting, StatusSetting
from app.settings import services
from querystring_parser import parser
from typing import List


class EntityManager(ABC):

    def __init__(self, amocrm: AmoCRM, session: Session) -> None:
        self._amocrm = amocrm
        self._session = session
        self._setting: CompanySetting = None
        self._status_settings: List[StatusSetting] = None
        # [{"id": ..., "field_id": ..., "value": ...}, ...]
        self._update_values = []
        self._update_leads_values = []

    @property
    @abstractmethod
    def setting(self):
        pass

    @property
    @abstractmethod
    def status_settings(self):
        pass

    @abstractmethod
    def set_field(self):
        pass

    @abstractmethod
    def set_many_fields(self):
        pass

    @abstractmethod
    def get_success_leads(self):
        pass

    def update_active_leads(self, leads: List[int], value: int):
        for lead in leads:
            self._update_leads_values.append(
                {"id": lead, "field_id": self.setting.lead_field_id, "value": value})
        if len(self._update_leads_values) > 0:
            self._amocrm.set_many_leads_field(self._update_leads_values)
            self._update_leads_values = []

    def update_or_append_values(self, entity_id, field_id, value):
        for update_value in self._update_values:
            if update_value['id'] == entity_id:
                update_value['custom_fields_values'].append(
                    {"field_id": field_id, "values": [{'value': value}]})
                return
        self._update_values.append(
            {"id": entity_id, "field_id": field_id, "value": value})

    def set_field_if_different(self, entity_id: int, field_id: int, value: int, entity_data):
        try:
            for custom_field in entity_data['custom_fields_values']:
                if int(custom_field['field_id']) == int(field_id):
                    if str(custom_field['values'][0]['value']) != str(value):
                        self.update_or_append_values(
                            entity_id, field_id, value)
                    return
            # если нет полей с таким id
            self._update_values.append(
                {"id": entity_id, "field_id": field_id, "value": value})
        except TypeError:
            return

    def apply_one_status_setting(self, entity_id: int, status_setting: StatusSetting, comparison_value: int, entity_data):
        if comparison_value <= status_setting.to_amount:
            if status_setting.from_amount is None:
                return self.set_field_if_different(
                    entity_id, status_setting.field_id, status_setting.status, entity_data)
            if comparison_value >= status_setting.from_amount:
                return self.set_field_if_different(
                    entity_id, status_setting.field_id, status_setting.status, entity_data)

    # pull up method

    def apply_status_settings(self, entity_id: int, sum_: int, amount: int, entity_data):
        for status_setting in self.status_settings:
            if status_setting.dependency_type == "quantity":
                self.apply_one_status_setting(
                    entity_id, status_setting, amount, entity_data)
            else:
                self.apply_one_status_setting(
                    entity_id, status_setting, sum_, entity_data)

    @abstractmethod
    def check(self):
        pass

    @abstractmethod
    def run_check(self):
        pass


class CompanyManager(EntityManager):
    @property
    def setting(self):
        if self._setting is None:
            self._setting = services.get_company_setting(self._session)
        return self._setting

    @property
    def status_settings(self):
        if self._status_settings is None:
            self._status_settings = services.get_status_settings_for_company(
                self._session)
        return self._status_settings

    def set_field(self, entity_id, field_id, value):
        return self._amocrm.set_company_field(entity_id, field_id, value)

    def set_many_fields(self):
        if len(self._update_values) > 0:
            self._amocrm.set_many_companies_field(self._update_values)
            self._update_values = []

    def get_success_leads(self, company_id: int, months: int):
        return self._amocrm.get_company_success_leads(company_id, months)

    def check(self, company_id, company_data):
        success_leads, active_leads, last_full_payment = self.get_success_leads(
            company_id, months=self.setting.months)
        sum_ = sum(success_leads)
        amount = len(success_leads)
        self.apply_status_settings(company_id, sum_, amount, company_data)

        if last_full_payment is not None:
            self.set_field(company_id, 1265119, last_full_payment)

        self.set_field_if_different(
            company_id, self.setting.company_field_id, sum_, company_data)
        self.update_active_leads(active_leads, sum_)

    def run_check(self):
        for company in self._amocrm.get_many_companies():
            self.check(company['id'], company)
        self.set_many_fields()


class ContactManager(EntityManager):
    @property
    def setting(self):
        if self._setting is None:
            self._setting = services.get_contact_setting(self._session)
        return self._setting

    @property
    def status_settings(self):
        if self._status_settings is None:
            self._status_settings = services.get_status_settings_for_contact(
                self._session)
        return self._status_settings

    def set_field(self, entity_id, field_id, value):
        return self._amocrm.set_contact_field(entity_id, field_id, value)

    def set_many_fields(self):
        if len(self._update_values) > 0:
            self._amocrm.set_many_contacts_field(self._update_values)
            self._update_values = []

    def get_success_leads(self, contact_id: int, months: int):
        return self._amocrm.get_contact_success_leads(contact_id, months)

    def check(self, contact_id, contact_data):
        success_leads, active_leads, _ = self.get_success_leads(
            contact_id, months=self.setting.months)
        sum_ = sum(success_leads)
        amount = len(success_leads)
        self.apply_status_settings(contact_id, sum_, amount, contact_data)
        self.set_field_if_different(
            contact_id, self.setting.contact_field_id, amount, contact_data)
        self.update_active_leads(active_leads, amount)

    def run_check(self):
        for contact in self._amocrm.get_many_contacts():
            self.check(contact['id'], contact)
        self.set_many_fields()


class HookHandler:
    def __init__(self, contact_manager: ContactManager, company_manager: CompanyManager, amocrm: AmoCRM) -> None:
        self._contact_manager = contact_manager
        self._company_manager = company_manager
        self._amocrm = amocrm
        # self._queue = queue
        self._lead_main_contact = None
        self._lead_company = None

    async def get_json_from_request(self, request: Request):
        if request.headers['Content-Type'] == 'application/x-www-form-urlencoded':
            data = await request.body()
            json_data = parser.parse(data, normalized=True)
            return json_data

    def get_lead_id_from_data(self, data):
        lead_id = list(data['leads'].items())[0][1][0]['id']
        return lead_id

    def get_lead_main_contact_id(self, lead):
        contacts = lead['_embedded']['contacts']
        for contact in contacts:
            if contact['is_main']:
                return contact['id']

    # У этого контакта есть только id и ссылка
    def get_contact_company_id(self, contact_id: int):

        contact_data = self._amocrm._make_request(
            "get", f"api/v4/contacts/{contact_id}")
        contact_companies = contact_data['_embedded']['companies']
        try:
            return contact_companies[0]['id'], contact_data
        except IndexError:
            return None, None

    def get_main_contact_and_company_ids(self, data):
        lead_id = self.get_lead_id_from_data(data)
        lead = self._amocrm._make_request(
            "get", f"api/v4/leads/{lead_id}", {"with": "contacts"})
        main_contact_id = self.get_lead_main_contact_id(lead)
        company_id, contact_data = self.get_contact_company_id(main_contact_id)
        return main_contact_id, company_id, contact_data

    def set_many_fields(self):
        self._company_manager.set_many_fields()
        self._contact_manager.set_many_fields()

    def handle(self, data):
        main_contact_id, company_id, contact_data = self.get_main_contact_and_company_ids(
            data)
        self._contact_manager.check(main_contact_id, contact_data)
        if company_id is not None:
            company_data = self._amocrm.get_company(company_id)
            self._company_manager.check(company_id, company_data)
        self.set_many_fields()
