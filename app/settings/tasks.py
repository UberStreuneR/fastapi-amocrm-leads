from app.worker import app
from app.integrations.deps import get_amocrm_from_first_integration
from app.settings.utils import ContactManager, CompanyManager, HookHandler
from sqlmodel import Session
from app.database import engine


@app.task(name="print_number", queue="settings")
def print_number(number: int):
    return number


@app.task(name="handle-hook", queue="settings")
def background_request(request_data):
    amocrm = get_amocrm_from_first_integration()
    with Session(engine) as session:
        contact_manager = ContactManager(amocrm, session)
        company_manager = CompanyManager(amocrm, session)

        handler = HookHandler(contact_manager, company_manager, amocrm)
        handler.handle(request_data)
        session.commit()


@app.task(name="run-contact-check", queue="settings")
def contact_check():
    amocrm = get_amocrm_from_first_integration()
    with Session(engine) as session:
        contact_manager = ContactManager(amocrm, session)
        contact_manager.run_check()
        session.commit()


@app.task(name="run-company-check", queue="settings")
def company_check():
    amocrm = get_amocrm_from_first_integration()
    with Session(engine) as session:
        company_manager = CompanyManager(amocrm, session)
        company_manager.run_check()
        session.commit()
