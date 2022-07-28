from fastapi import APIRouter, Depends, Request
from app.amocrm import AmoCRM
from app.integrations.deps import get_amocrm_from_first_integration, get_amocrm, get_auth_data, get_session
from app.settings.schemas import ContactSetting, CompanySetting, StatusSetting
from app.settings_ import settings
from app.settings.schemas import StatusSetting
from app.settings import services
from sqlmodel import Session
from typing import List
from fastapi import BackgroundTasks, Response
from fastapi import status
from querystring_parser import parser
from app.settings.tasks import company_check, contact_check, background_request

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


# @router.post("/run-contact-check")
# def run_contact_check(amocrm: AmoCRM = Depends(get_amocrm), session: Session = Depends(get_session)):
#     manager = ContactManager(amocrm, session)
#     manager.run_check()


# @router.post("/run-company-check")
# def run_company_check(amocrm: AmoCRM = Depends(get_amocrm), session: Session = Depends(get_session)):
#     manager = CompanyManager(amocrm, session)
#     manager.run_check()

@router.post("/run-contact-check")
def run_contact_check():
    contact_check.apply()
    # manager = ContactManager(amocrm, session)
    # manager.run_check()


@router.post("/run-company-check")
def run_company_check():
    company_check.apply()
    # manager = CompanyManager(amocrm, session)
    # manager.run_check()


# async def background_request(request_data, amocrm, session):
#     contact_manager = ContactManager(amocrm, session)
#     company_manager = CompanyManager(amocrm, session)

#     handler = HookHandler(contact_manager, company_manager, amocrm)
#     await handler.handle(request_data)


@router.post("/handle-hook")
async def handle_hook(request: Request, background_tasks: BackgroundTasks):
    if request.headers['Content-Type'] == 'application/x-www-form-urlencoded':
        data = await request.body()
        json_data = parser.parse(data, normalized=True)
        background_request.delay(json_data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
