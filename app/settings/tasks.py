from app.worker import app
from app.integrations.deps import get_amocrm_from_first_integration
from .utils import ContactManager, CompanyManager, HookHandler
from app.database import get_session
from .task_classes import ContactCheck, CompanyCheck


@app.task
def handle_hook_on_background(request_data, ignore_result=True) -> None:
    amocrm = get_amocrm_from_first_integration()
    session = next(get_session())
    contact_manager = ContactManager(amocrm, session)
    company_manager = CompanyManager(amocrm, session)

    handler = HookHandler(contact_manager, company_manager, amocrm)
    handler.handle(request_data)


@app.task(base=ContactCheck, bind=True, ignore_result=True)
def contact_check(self) -> None:
    contact_manager = ContactManager(self.amocrm, self.session)
    contact_manager.run_check()


@app.task(base=CompanyCheck, bind=True, ignore_result=True)
def company_check(self) -> None:
    company_manager = CompanyManager(self.amocrm, self.session)
    company_manager.run_check()
