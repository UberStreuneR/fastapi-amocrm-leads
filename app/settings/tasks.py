from app.worker import app
from app.integrations.deps import get_amocrm_from_first_integration
from .hook import HookHandler
from .entity_checkers import ContactChecker, CompanyChecker
from .task_classes import ContactCheckTask, CompanyCheckTask


@app.task(ignore_result=True)
def handle_hook_on_background(request_data) -> None:
    amocrm = get_amocrm_from_first_integration()
    handler = HookHandler(amocrm)
    handler.handle(request_data)


@app.task(base=ContactCheckTask, bind=True, ignore_result=True)
def contact_check(self) -> None:
    contact_checker = ContactChecker(self.amocrm)
    contact_checker.run_check()


@app.task(base=CompanyCheckTask, bind=True, ignore_result=True)
def company_check(self) -> None:
    company_checker = CompanyChecker(self.amocrm)
    company_checker.run_check()
