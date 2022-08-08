from __future__ import annotations
from abc import ABC, abstractmethod

from .schemas import CompanySetting, ContactSetting, StatusSetting
from . import services
from app.amocrm.managers import EntityManager, LeadManager
from sqlmodel import Session

from typing import List, Union, Tuple

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


class EntityChecker(ABC):
    """Базовый класс для проверки сущностей на соответствие настройкам"""

    def __init__(self, manager: EntityManager, lead_manager: LeadManager, session: Session) -> None:
        self._setting: CompanySetting = None
        self._status_settings: List[StatusSetting] = None
        # [{"id": ..., "field_id": ..., "value": ...}, ...]
        self._update_values = []
        self._update_leads_values = []
        self._lead_manager = lead_manager
        self._manager = manager
        self._session = session

    @property
    @abstractmethod
    def setting(self):
        """Настройки со страниц для компании и контакта"""
        pass

    @property
    @abstractmethod
    def status_settings(self):
        """Настройки со страницы Статус клиента"""
        pass

    def set_field(self, entity_id, field_id, value) -> dict:
        """Установить поле сущности. Паттерн Стратегия для менеджера сущности"""
        return self._manager.set_field(entity_id, field_id, value)

    def set_many_fields(self) -> None:
        """Установить поля для нескольких сущностей."""

        if len(self._update_values) > 0:
            self._manager.set_many_fields(self._update_values)
            self._update_values = []

    def get_success_leads(self, entity_id: int, months: int) -> Tuple[List[dict], List[int], Union[int, None]]:
        """Получить успешные сделки сущности контакт или компания"""
        return self._manager.get_success_leads(entity_id, months)

    def update_active_leads(self, leads: List[int], value: int) -> None:
        """Обновить поля активных сделок"""

        for lead in leads:
            self._update_leads_values.append(
                {"id": lead, "field_id": self.setting.lead_field_id, "value": value})
        if len(self._update_leads_values) > 0:
            self._lead_manager.set_many_fields(self._update_leads_values)
            self._update_leads_values.clear()

    def update_or_append_values(self, entity_id, field_id, value) -> None:
        """Добавить значение на обновление сущностей"""

        logger.info(f"Update values: {self._update_values}")
        for update_value in self._update_values:
            if update_value["id"] == entity_id:
                update_value["custom_fields_values"].append(
                    {"field_id": field_id, "values": [{"value": value}]})
                return
        self._update_values.append(
            {"id": entity_id, "custom_fields_values": [{"field_id": field_id, "values": [{"value": value}]}]})

    def set_field_if_different(self, entity_id: int, field_id: int, value: Union[str, int], entity_data) -> None:
        """Добавить значение на обновление, если оно отлично от текущего"""

        try:
            if entity_data["custom_fields_values"] is None:
                self.update_or_append_values(
                    entity_id, field_id, value)
                return
            for custom_field in entity_data["custom_fields_values"]:
                if int(custom_field["field_id"]) == int(field_id):
                    if str(custom_field["values"][0]["value"]) != str(value):
                        self.update_or_append_values(
                            entity_id, field_id, value)
                    else:
                        logger.info(
                            f"\nValues equal: {custom_field['values'][0]['value']} == {value}")
                    return
            # если нет полей с таким id
            # self._update_values.append(
            #     {"id": entity_id, "field_id": field_id, "value": value})
            self.update_or_append_values(
                entity_id, field_id, value)
        except TypeError:
            logger.info(
                f"\nTypeError:\nentity_id: {entity_id}\nvalue: {value}\n\ndata:\n{entity_data}\n\n\n")

    def apply_one_status_setting(self, entity_id: int, status_setting: StatusSetting, comparison_value: int, entity_data) -> None:
        """Сравнить переданное значение с настройкой Статуса клиента и добавить на обновление в случае успеха"""

        logger.info(
            f"Applying one status setting.\nstatus_setting: {status_setting}\n\ncomparison: {comparison_value}\ndata:\n\n{entity_data}\n\n\n")

        if comparison_value <= status_setting.to_amount:
            if status_setting.from_amount is None:
                self.set_field_if_different(
                    entity_id, status_setting.field_id, status_setting.status, entity_data)
                return
            if comparison_value >= status_setting.from_amount:
                self.set_field_if_different(
                    entity_id, status_setting.field_id, status_setting.status, entity_data)

    def apply_status_settings(self, entity_id: int, sum_: int, amount: int, entity_data) -> None:
        """Сравнить переданное значение со всеми настройками Статуса клиента в зависимости от типа зависимости"""

        logger.info(
            f"\n\n\nApplying status settings:\nsum: {sum_}\namount: {amount}\n, data:\n{entity_data}\n\nstatus settings:\n{self.status_settings}\n\n\n")
        for status_setting in self.status_settings:
            if status_setting.dependency_type == "quantity":
                self.apply_one_status_setting(
                    entity_id, status_setting, amount, entity_data)
            else:
                self.apply_one_status_setting(
                    entity_id, status_setting, sum_, entity_data)

    @abstractmethod
    def check(self):
        """Запустить проверку для сущности"""

        pass

    @abstractmethod
    def run_check(self):
        """Запустить проверку для всех сущностей"""

        pass


class CompanyChecker(EntityChecker):
    """Класс для проверки компаний"""

    @property
    def setting(self) -> CompanySetting:
        if self._setting is None:
            self._setting = services.get_company_setting(self._session)
        return self._setting

    @property
    def status_settings(self) -> List[StatusSetting]:
        if self._status_settings is None:
            self._status_settings = services.get_status_settings_for_company(
                self._session)
        return self._status_settings

    def check(self, company_id, company_data) -> None:
        success_leads, active_leads, last_full_payment = self.get_success_leads(
            company_id, months=self.setting.months)
        sum_ = sum(success_leads)
        amount = len(success_leads)
        self.apply_status_settings(company_id, sum_, amount, company_data)

        # if last_full_payment is not None:
        # self.set_field(
        # company_id, settings.company_last_payment_field, last_full_payment)

        self.set_field_if_different(
            company_id, self.setting.company_field_id, sum_, company_data)
        self.update_active_leads(active_leads, sum_)

    def run_check(self) -> None:
        for company in self._amocrm.get_many_companies():
            self.check(company["id"], company)
        self.set_many_fields()


class ContactChecker(EntityChecker):
    """Класс для проверки контактов"""

    @property
    def setting(self) -> ContactSetting:
        if self._setting is None:
            self._setting = services.get_contact_setting(self._session)
        return self._setting

    @property
    def status_settings(self) -> List[StatusSetting]:
        if self._status_settings is None:
            self._status_settings = services.get_status_settings_for_contact(
                self._session)
        return self._status_settings

    def check(self, contact_id, contact_data) -> None:
        success_leads, active_leads = self.get_success_leads(
            contact_id, months=self.setting.months)
        sum_ = sum(success_leads)
        amount = len(success_leads)
        self.apply_status_settings(contact_id, sum_, amount, contact_data)
        self.set_field_if_different(
            contact_id, self.setting.contact_field_id, amount, contact_data)
        self.update_active_leads(active_leads, amount)

    def run_check(self) -> None:
        for contact in self._amocrm.get_many_contacts():
            self.check(contact["id"], contact)
        self.set_many_fields()
