from fastapi import APIRouter, Depends

from amocrm import AmoCRM
from settings.schemas import ContactSetting, CompanySetting, StatusSetting
from integrations.deps import get_amocrm
from settings_ import settings
from settings.schemas import StatusSetting
from settings import services
from integrations.deps import get_session
from sqlmodel import Session
from typing import List

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/")
def test_function(amocrm: AmoCRM = Depends(get_amocrm)):
    result = amocrm._make_test_request()
    return result


@router.get("/settings-object")
def get_settings_object():
    return settings.dict()


@router.get("/status", status_code=200, response_model=List[StatusSetting])
def get_status_settings(session: Session = Depends(get_session)):
    return services.get_status_settings(session)


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


@router.get("/run-contact-check")
def run_contact_check(amocrm: AmoCRM = Depends(get_amocrm), session: Session = Depends(get_session)):
    contact_setting = services.get_contact_setting(session)
    status_settings = services.get_status_settings(session)
    # TODO


@router.get("/get-custom-fields")
def get_entity_fields(amocrm: AmoCRM = Depends(get_amocrm)):
    return amocrm.get_custom_fields()
