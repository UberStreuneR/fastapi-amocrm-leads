from __future__ import annotations
from abc import ABC, abstractmethod

from starlette.requests import ClientDisconnect
from fastapi import Request
from app.amocrm import AmoCRM
from sqlmodel import Session
from app.settings.schemas import CompanySetting, ContactSetting, StatusSetting
from app.settings import services
from querystring_parser import parser
from typing import List


class EntityManager(ABC):

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

    @abstractmethod
    def update_active_leads(self):
        pass

    @abstractmethod
    def set_field_if_different(self):
        pass

    @abstractmethod
    def apply_one_status_setting(self):
        pass

    @abstractmethod
    def apply_status_settings(self):
        pass

    @abstractmethod
    def check(self):
        pass

    @abstractmethod
    def run_check(self):
        pass


class CompanyManager(EntityManager):

    def __init__(self, amocrm: AmoCRM, session: Session) -> None:
        self._amocrm = amocrm
        self._session = session
        self._setting: CompanySetting = None
        self._status_settings: List[StatusSetting] = None
        # [{"id": ..., "field_id": ..., "value": ...}, ...]
        self._update_values = []
        self._update_leads_values = []

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
        if len(self._update_values > 0):
            self._amocrm.set_many_companies_field(self._update_values)
            self._update_values = []

    def get_success_leads(self, company_id: int, months: int):
        return self._amocrm.get_company_success_leads(company_id, months)

    def update_active_leads(self, leads: List[int], sum_: int):
        for lead in leads:
            # self._amocrm.set_lead_field(lead,
            #                             self.setting.lead_field_id, sum_)
            self._update_leads_values.append(
                {"id": lead, "field_id": self.setting.lead_field_id, "value": sum_})
        self._amocrm.set_many_leads_field(self._update_leads_values)
        self._update_leads_values = []

    def set_field_if_different(self, company_id: int, field_id: int, value: int, company_data):
        for custom_field in company_data['custom_fields_values']:
            if custom_field['field_id'] == field_id:
                if custom_field['values'][0]['value'] != value:
                    self._update_values.append(
                        {"id": company_id, "field_id": field_id, "value": value})
                    break
    # comparison_value является либо суммой, либо количеством

    def apply_one_status_setting(self, company_id: int, status_setting: StatusSetting, comparison_value: int, company_data):
        if comparison_value >= status_setting.from_amount and comparison_value <= status_setting.to_amount:
            self.set_field_if_different(
                company_id, status_setting.field_id, status_setting.status, company_data)

    def apply_status_settings(self, company_id: int, sum_: int, amount: int, company_data):
        for status_setting in self.status_settings:
            if status_setting.dependency_type == "quantity":
                self.apply_one_status_setting(
                    company_id, status_setting, amount, company_data)
            else:
                self.apply_one_status_setting(
                    company_id, status_setting, sum_, company_data)

    def check(self, company_id, company_data):
        success_leads, active_leads = self.get_success_leads(
            company_id, months=self.setting.months)
        sum_ = sum(success_leads)
        amount = len(success_leads)
        self.apply_status_settings(company_id, sum_, amount, company_data)

        # TODO: Оплачено == Последняя оплата компании

        self.set_field_if_different(
            company_id, self.setting.company_field_id, sum_, company_data)
        self.update_active_leads(active_leads, sum_)

    def run_check(self):
        for company in self._amocrm.get_many_companies():
            try:
                self.check(company['id'], company)
            except ClientDisconnect:
                self.check(company['id'], company)
        self.set_many_fields()


class ContactManager(EntityManager):

    def __init__(self, amocrm: AmoCRM, session: Session) -> None:
        self._amocrm = amocrm
        self._session = session
        self._setting: ContactSetting = None
        self._status_settings: List[StatusSetting] = None
        # [{"id": ..., "field_id": ..., "value": ...}, ...]
        self._update_values = []
        self._update_leads_values = []

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
        if len(self._update_values > 0):
            print(f"\n\nUPDATE_VALUES: {self._update_values}\n\n")
            self._amocrm.set_many_contacts_field(self._update_values)
            self._update_values = []

    def get_success_leads(self, contact_id: int, months: int):
        return self._amocrm.get_contact_success_leads(contact_id, months)

    def update_active_leads(self, leads: List[int], amount: int):
        # for lead in leads:
        #     self._amocrm.set_lead_field(lead,
        #                                 self.setting.lead_field_id, amount)
        for lead in leads:
            self._update_leads_values.append(
                {"id": lead, "field_id": self.setting.lead_field_id, "value": amount})
        self._amocrm.set_many_leads_field(self._update_leads_values)
        self._update_leads_values = []

    def set_field_if_different(self, contact_id: int, field_id: int, value: int, contact_data):
        for custom_field in contact_data['custom_fields_values']:
            if custom_field['field_id'] == field_id:
                if custom_field['values'][0]['value'] != value:
                    self._update_values.append(
                        {"id": contact_id, "field_id": field_id, "value": value})
                    break

    # comparison_value является либо суммой, либо количеством
    def apply_one_status_setting(self, contact_id: int, status_setting: StatusSetting, comparison_value: int, contact_data):
        if comparison_value >= status_setting.from_amount and comparison_value <= status_setting.to_amount:
            # self.set_field(contact_id,
            #    status_setting.field_id, status_setting.status)
            self.set_field_if_different(
                contact_id, status_setting.field_id, status_setting.status, contact_data)
            # self._update_values.append(
            # {"id": contact_id, "field_id": status_setting.field_id, "value": status_setting.status})

    def apply_status_settings(self, contact_id: int, sum_: int, amount: int, contact_data):
        for status_setting in self.status_settings:
            if status_setting.dependency_type == "quantity":
                self.apply_one_status_setting(
                    contact_id, status_setting, amount, contact_data)
            else:
                self.apply_one_status_setting(
                    contact_id, status_setting, sum_, contact_data)

    def check(self, contact_id, contact_data):
        success_leads, active_leads = self.get_success_leads(
            contact_id, months=self.setting.months)
        sum_ = sum(success_leads)
        amount = len(success_leads)
        self.apply_status_settings(contact_id, sum_, amount, contact_data)
        # self.set_field(contact_id, self.setting.contact_field_id, amount)
        self.set_field_if_different(
            contact_id, self.setting.contact_field_id, amount, contact_data)
        # self._update_values.append(
        #     {"id": contact_id, "field_id": self.setting.contact_field_id, "value": amount})
        self.update_active_leads(active_leads, amount)

    def run_check(self):
        for contact in self._amocrm.get_many_contacts():
            try:
                self.check(contact['id'], contact)
            except ClientDisconnect:
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
            return None

    def get_main_contact_and_company_ids(self, data):
        lead_id = self.get_lead_id_from_data(data)
        lead = self._amocrm._make_request(
            "get", f"api/v4/leads/{lead_id}", {"with": "contacts"})
        main_contact_id, contact_data = self.get_lead_main_contact_id(lead)
        company_id = self.get_contact_company_id(main_contact_id)
        return main_contact_id, company_id, contact_data

    def handle(self, data):
        main_contact_id, company_id, contact_data = self.get_main_contact_and_company_ids(
            data)
        self._contact_manager.check(main_contact_id, contact_data)
        if company_id is not None:
            company_data = self._amocrm.get_company(company_id)
            self._company_manager.check(company_id, company_data)
