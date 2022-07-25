from __future__ import annotations
from abc import ABC, abstractmethod
from amocrm import AmoCRM
from sqlmodel import Session
from settings.schemas import CompanySetting, ContactSetting, StatusSetting
from settings import services
from typing import List


class EntityChecker(ABC):

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
    def update_active_leads(self):
        pass

    @abstractmethod
    def apply_one_status_setting(self):
        pass

    @abstractmethod
    def apply_status_settings(self):
        pass

    @abstractmethod
    def run_check(self):
        pass


class CompanyChecker(EntityChecker):

    def __init__(self, amocrm: AmoCRM, session: Session) -> None:
        self._amocrm = amocrm
        self._session = session
        self._setting: CompanySetting = None
        self._status_settings: List[StatusSetting] = None

    @property
    def setting(self):
        if self._setting is None:
            return services.get_company_setting(self._session)
        return self._setting

    @property
    def status_settings(self):
        if self._status_settings is None:
            return services.get_status_settings_for_company(self._session)
        return self._status_settings

    def set_field(self, entity_id, field_id, value):
        return self._amocrm.set_company_field(entity_id, field_id, value)

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

    def run_check(self):
        for company in self._amocrm.get_many_companies():
            company_id = company['id']
            success_leads, active_leads = self._amocrm.get_company_success_leads(
                company_id, months=self.setting.months)
            sum_ = sum(success_leads)
            amount = len(success_leads)
            self.apply_status_settings(company_id, sum_, amount)
            self.set_field(company_id, self.setting.company_field_id, sum_)
            self.update_active_leads(active_leads, sum_)


class ContactChecker(EntityChecker):

    def __init__(self, amocrm: AmoCRM, session: Session) -> None:
        self._amocrm = amocrm
        self._session = session
        self._setting: ContactSetting = None
        self._status_settings: List[StatusSetting] = None

    @property
    def setting(self):
        if self._setting is None:
            return services.get_contact_setting(self._session)
        return self._setting

    @property
    def status_settings(self):
        if self._status_settings is None:
            return services.get_status_settings_for_contact(self._session)
        return self._status_settings

    def set_field(self, entity_id, field_id, value):
        return self._amocrm.set_contact_field(entity_id, field_id, value)

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

    def run_check(self):
        for contact in self._amocrm.get_many_contacts():
            contact_id = contact['id']
            success_leads, active_leads = self._amocrm.get_contact_success_leads(
                contact_id, months=self.setting.months)
            sum_ = sum(success_leads)
            amount = len(success_leads)
            self.apply_status_settings(contact_id, sum_, amount)
            self.set_field(contact_id, self.setting.contact_field_id, amount)
            self.update_active_leads(active_leads, amount)
