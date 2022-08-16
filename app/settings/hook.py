from __future__ import annotations

from app.amocrm.base import AmoCRM
from .entity_checkers import ContactChecker, CompanyChecker
from app.amocrm.managers import ContactManager, CompanyManager, LeadManager, MetaManager
from app.amocrm.helpers import get_lead_id_from_data, get_lead_main_contact_id

from sqlmodel import Session
from typing import Tuple

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


class HookHandler:
    """Класс для обработки хука на обновление сделки"""

    def __init__(self, amocrm: AmoCRM, session: Session) -> None:
        self.manager = MetaManager(amocrm, session)
        self._contact_checker = ContactChecker(
            self.manager.contacts, self.manager.leads, session)
        self._company_checker = CompanyChecker(
            self.manager.companies, self.manager.leads, session)

    # У этого контакта есть только id и ссылка

    def get_contact_company_id(self, contact_id: int) -> Tuple[str, dict] | Tuple[None, None]:
        """Получить id компании, прикрепленной к контакту"""

        if contact_id is None:
            return None, None
        contact_data = self.manager.contacts.get_one(contact_id)
        contact_companies = contact_data["_embedded"]["companies"]
        try:
            return contact_companies[0]["id"], contact_data
        except IndexError:
            if contact_data:
                return None, contact_data
            return None, None

    def get_main_contact_and_company_ids(self, data) -> Tuple[int, int, dict | None]:
        """Получить id контакта и id его компании"""

        lead_id = get_lead_id_from_data(data)
        lead = self.manager.leads.get_one(lead_id)
        main_contact_id = get_lead_main_contact_id(lead)
        company_id, contact_data = self.get_contact_company_id(main_contact_id)
        return main_contact_id, company_id, contact_data

    def set_many_fields(self) -> None:
        """Установить сравненные с настройками поля для сущностей"""

        self._company_checker.set_many_fields()
        self._contact_checker.set_many_fields()

    def handle(self, data) -> None:
        """Провести проверку контакта и компании, если она есть"""

        main_contact_id, company_id, contact_data = self.get_main_contact_and_company_ids(
            data)
        if main_contact_id is not None:
            self._contact_checker.check(main_contact_id, contact_data)
        if company_id is not None:
            company_data = self.manager.companies.get_one(company_id)
            self._company_checker.check(company_id, company_data)
        self.set_many_fields()
