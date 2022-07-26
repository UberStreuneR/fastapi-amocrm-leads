from __future__ import annotations
from abc import ABC, abstractmethod

from fastapi import Request
from pip import main
from amocrm import AmoCRM
from sqlmodel import Session
from settings.schemas import CompanySetting, ContactSetting, StatusSetting
from settings import services
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
    def get_success_leads(self):
        pass

    @abstractmethod
    def update_active_leads(self):
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

    def get_success_leads(self, company_id: int, months: int):
        return self._amocrm.get_company_success_leads(company_id, months)

    def update_active_leads(self, leads: List[int], sum_: int):
        for lead in leads:
            self._amocrm.set_lead_field(lead,
                                        self.setting.lead_field_id, sum_)

    # comparison_value is either a sum or an amount
    def apply_one_status_setting(self, company_id: int, status_setting: StatusSetting, comparison_value: int):
        if comparison_value >= status_setting.from_amount and comparison_value <= status_setting.to_amount:
            self.set_field(company_id,
                           status_setting.field_id, status_setting.status)

    def apply_status_settings(self, company_id: int, sum_: int, amount: int):
        for status_setting in self.status_settings:
            if status_setting.dependency_type == "quantity":
                self.apply_one_status_setting(
                    company_id, status_setting, amount)
            else:
                self.apply_one_status_setting(
                    company_id, status_setting, sum_)

    def check(self, company_id):
        success_leads, active_leads = self.get_success_leads(
            company_id, months=self.setting.months)
        sum_ = sum(success_leads)
        amount = len(success_leads)
        self.apply_status_settings(company_id, sum_, amount)
        self.set_field(company_id, self.setting.company_field_id, sum_)
        self.update_active_leads(active_leads, sum_)

    def run_check(self):
        for company in self._amocrm.get_many_companies():
            self.check(company['id'])


class ContactManager(EntityManager):

    def __init__(self, amocrm: AmoCRM, session: Session) -> None:
        self._amocrm = amocrm
        self._session = session
        self._setting: ContactSetting = None
        self._status_settings: List[StatusSetting] = None

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

    def get_success_leads(self, contact_id: int, months: int):
        return self._amocrm.get_contact_success_leads(contact_id, months)

    def update_active_leads(self, leads: List[int], amount: int):
        for lead in leads:
            self._amocrm.set_lead_field(lead,
                                        self.setting.lead_field_id, amount)

    # comparison_value is either a sum or an amount
    def apply_one_status_setting(self, contact_id: int, status_setting: StatusSetting, comparison_value: int):
        if comparison_value >= status_setting.from_amount and comparison_value <= status_setting.to_amount:
            self.set_field(contact_id,
                           status_setting.field_id, status_setting.status)

    def apply_status_settings(self, contact_id: int, sum_: int, amount: int):
        for status_setting in self.status_settings:
            if status_setting.dependency_type == "quantity":
                self.apply_one_status_setting(
                    contact_id, status_setting, amount)
            else:
                self.apply_one_status_setting(
                    contact_id, status_setting, sum_)

    def check(self, contact_id):
        success_leads, active_leads = self.get_success_leads(
            contact_id, months=self.setting.months)
        sum_ = sum(success_leads)
        amount = len(success_leads)
        self.apply_status_settings(contact_id, sum_, amount)
        self.set_field(contact_id, self.setting.contact_field_id, amount)
        self.update_active_leads(active_leads, amount)

    def run_check(self):
        for contact in self._amocrm.get_many_contacts():
            self.check(contact['id'])


class HookHandler:
    def __init__(self, contact_manager: ContactManager, company_manager: CompanyManager, amocrm: AmoCRM) -> None:
        self._contact_manager = contact_manager
        self._company_manager = company_manager
        self._amocrm = amocrm
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

    # this contact only has id and link, it's not a complete data of a contact entity
    def get_contact_company_id(self, contact_id: int):

        contact_data = self._amocrm._make_request(
            "get", f"api/v4/contacts/{contact_id}")
        contact_companies = contact_data['_embedded']['companies']
        try:
            return contact_companies[0]['id']
        except IndexError:
            return None

    def get_main_contact_and_company_ids(self, data):
        lead_id = self.get_lead_id_from_data(data)
        lead = self._amocrm._make_request(
            "get", f"api/v4/leads/{lead_id}", {"with": "contacts"})
        main_contact_id = self.get_lead_main_contact_id(lead)
        company_id = self.get_contact_company_id(main_contact_id)
        return main_contact_id, company_id

    async def handle(self, request: Request):
        data = await self.get_json_from_request(request)
        main_contact_id, company_id = self.get_main_contact_and_company_ids(
            data)

        self._contact_manager.check(main_contact_id)
        if company_id is not None:
            self._company_manager.check(company_id)
