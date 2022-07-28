from app.worker import app
from app.integrations.deps import get_amocrm_from_first_integration
from app.settings.utils import ContactManager, CompanyManager, HookHandler
from sqlmodel import Session
from app.database import engine


@app.task
def background_request(request_data):
    amocrm = get_amocrm_from_first_integration()
    with Session(engine) as session:
        contact_manager = ContactManager(amocrm, session)
        company_manager = CompanyManager(amocrm, session)

        handler = HookHandler(contact_manager, company_manager, amocrm)
        handler.handle(request_data)
        session.commit()


@app.task
def contact_check():
    amocrm = get_amocrm_from_first_integration()
    with Session(engine) as session:
        contact_manager = ContactManager(amocrm, session)
        contact_manager.run_check()
        session.commit()


@app.task
def company_check():
    amocrm = get_amocrm_from_first_integration()
    with Session(engine) as session:
        company_manager = CompanyManager(amocrm, session)
        company_manager.run_check()
        session.commit()
