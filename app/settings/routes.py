from cgitb import Hook
from fastapi import APIRouter, Depends, Request
from starlette.requests import ClientDisconnect

from amocrm import AmoCRM
from integrations.deps import get_amocrm_from_first_integration
from settings.schemas import ContactSetting, CompanySetting, StatusSetting
from integrations.deps import get_amocrm, get_auth_data
from settings_ import settings
from settings.schemas import StatusSetting
from settings import services
from integrations.deps import get_session
from sqlmodel import Session
from typing import List
from settings.utils import CompanyManager, ContactManager, HookHandler, Queue

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/settings-object")
def get_settings_object():
    return settings.dict()


@router.get("/status", status_code=200, response_model=List[StatusSetting])
def get_status_settings(session: Session = Depends(get_session)):
    return services.get_status_settings(session)


@router.get("/custom-status", status_code=200)
def get_custom_status_settings(session: Session = Depends(get_session)):
    data = {
        "company": services.get_status_settings_for_company(session),
        "contact": services.get_status_settings_for_contact(session)
    }
    return data


@router.post("/status", status_code=201)
def save_status_settings(status_settings: List[StatusSetting], session: Session = Depends(get_session)):
    return services.save_status_settings(session, status_settings)


@router.get("/contact", status_code=200, response_model=ContactSetting)
def get_contact_setting(session: Session = Depends(get_session)):
    return services.get_contact_setting(session)


@router.post("/contact", status_code=201)
def set_contact_setting(contact_setting: ContactSetting, session: Session = Depends(get_session)):
    return services.set_contact_setting(session, contact_setting)


@router.get("/company", status_code=200, response_model=CompanySetting)
def get_company_setting(session: Session = Depends(get_session)):
    return services.get_company_setting(session)


@router.post("/company", status_code=201)
def set_company_setting(company_setting: CompanySetting, session: Session = Depends(get_session)):
    return services.set_company_setting(session, company_setting)


@router.get("/get-custom-fields")
def get_entity_fields(amocrm: AmoCRM = Depends(get_amocrm)):
    return amocrm.get_custom_fields()


@router.post("/run-contact-check")
def run_contact_check(amocrm: AmoCRM = Depends(get_amocrm), session: Session = Depends(get_session)):
    manager = ContactManager(amocrm, session)
    manager.run_check()


@router.post("/run-company-check")
def run_company_check(amocrm: AmoCRM = Depends(get_amocrm), session: Session = Depends(get_session)):
    manager = CompanyManager(amocrm, session)
    manager.run_check()


@router.post("/handle-hook")
async def handle_hook(request: Request, amocrm: AmoCRM = Depends(get_amocrm_from_first_integration), session: Session = Depends(get_session)):

    queue = Queue()
    queue.add_hook(request)

    contact_manager = ContactManager(amocrm, session)
    company_manager = CompanyManager(amocrm, session)

    handler = HookHandler(contact_manager, company_manager, amocrm, queue)
    try:
        await handler.handle()
    except ClientDisconnect:
        await handler.handle()
