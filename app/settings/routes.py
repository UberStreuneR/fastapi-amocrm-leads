from fastapi import APIRouter, Depends, Request, Response, status

from app.amocrm.base import AmoCRM
from app.integrations.deps import get_amocrm, get_session
from .schemas import ContactSetting, CompanySetting, StatusSetting
from app.app_settings import get_settings
from app.settings.schemas import StatusSetting
from . import services
from .tasks import company_check, contact_check, handle_hook_on_background
from app.amocrm.managers import MetaManager

from sqlmodel import Session
from typing import List
from querystring_parser import parser

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/settings-object")
def get_settings_object():
    """Получить настройки приложения"""

    return get_settings().dict()


@router.get("/status", status_code=200, response_model=List[StatusSetting])
def get_status_settings(session: Session = Depends(get_session)):
    """Получить настройки Статуса клиента"""

    return services.get_status_settings(session)


@router.get("/custom-status", status_code=200)
def get_custom_status_settings(session: Session = Depends(get_session)):
    """Получить настройки Статуса клиента для компаний и контактов"""
    data = {
        "company": services.get_status_settings_for_company(session),
        "contact": services.get_status_settings_for_contact(session)
    }
    return data


@router.post("/status", status_code=201)
def save_status_settings(status_settings: List[StatusSetting], session: Session = Depends(get_session)):
    """Сохранить настройки Статуса клиента"""
    return services.save_status_settings(session, status_settings)


@router.get("/contact", status_code=200, response_model=ContactSetting)
def get_contact_setting(session: Session = Depends(get_session)):
    """Получить настройки для проверки контакта"""
    return services.get_contact_setting(session)


@router.post("/contact", status_code=201)
def set_contact_setting(contact_setting: ContactSetting, session: Session = Depends(get_session)):
    """Установить настройки для проверки контакта"""
    return services.set_contact_setting(session, contact_setting)


@router.get("/company", status_code=200, response_model=CompanySetting)
def get_company_setting(session: Session = Depends(get_session)):
    """Получить настройки для проверки компании"""
    return services.get_company_setting(session)


@router.post("/company", status_code=201)
def set_company_setting(company_setting: CompanySetting, session: Session = Depends(get_session)):
    """Установить настройки для проверки компании"""
    return services.set_company_setting(session, company_setting)


@router.get("/get-custom-fields")
def get_entity_fields(amocrm: AmoCRM = Depends(get_amocrm)):
    """Получить кастомные поля всех сущностей"""
    manager = MetaManager(amocrm)
    return manager.get_custom_fields()


@router.post("/run-contact-check")
def run_contact_check():
    """Запустить проверку контактов"""
    contact_check.delay()


@router.post("/run-company-check")
def run_company_check():
    """Запустить проверку компаний"""
    company_check.delay()


@router.post("/handle-hook")
async def handle_hook(request: Request):
    """Обработать хук"""

    if request.headers["Content-Type"] == "application/x-www-form-urlencoded":
        data = await request.body()
        json_data = parser.parse(data, normalized=True)
        handle_hook_on_background.delay(json_data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/contact-check-status")
def contact_check_status(session: Session = Depends(get_session)):
    """Проверить, запущена ли проверка контакта"""
    return services.get_contact_check_status(session)


@router.get("/company-check-status")
def company_check_status(session: Session = Depends(get_session)):
    """Проверить, запущена ли проверка компании"""
    return services.get_company_check_status(session)
