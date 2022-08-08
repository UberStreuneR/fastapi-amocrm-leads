from app.worker import app
from app.integrations.deps import get_amocrm_from_first_integration
from .hook import HookHandler
from .entity_checkers import ContactChecker, CompanyChecker
from .task_classes import EntityCheck, ContactCheckTask, CompanyCheckTask
from app.database import get_session
from app.amocrm.managers import ContactManager, CompanyManager


@app.task(base=EntityCheck, bind=True, ignore_result=True)
def handle_hook_on_background(self, request_data) -> None:
    handler = HookHandler(self.amocrm, self.session)
    handler.handle(request_data)


@app.task(base=ContactCheckTask, bind=True, ignore_result=True)
def contact_check(self) -> None:
    contact_checker = ContactChecker(
        self.manager, self.lead_manager, self.session)
    contact_checker.run_check()


@app.task(base=CompanyCheckTask, bind=True, ignore_result=True)
def company_check(self) -> None:
    company_checker = CompanyChecker(
        self.manager, self.lead_manager, self.session)
    company_checker.run_check()
