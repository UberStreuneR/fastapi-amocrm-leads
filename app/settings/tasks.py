from app.worker import app
from app.integrations.deps import get_amocrm_from_first_integration
from app.settings.utils import ContactManager, CompanyManager, HookHandler
from sqlmodel import Session
from app.database import engine
from app.settings import services
import time


class EntityCheck(app.Task):
    _number = 42

    def before_start(self, *args, **kwargs):
        self.session = Session(engine)
        self.amocrm = get_amocrm_from_first_integration()

    def after_return(self, *args, **kwargs):
        self.session.commit()


class ContactCheck(EntityCheck):

    def before_start(self, *args, **kwargs):
        super().before_start(*args, **kwargs)
        services.set_contact_check_status(self.session, True)
        self.session.commit()

    def after_return(self, *args, **kwargs):
        services.set_contact_check_status(self.session, False)
        super().after_return(*args, **kwargs)


class CompanyCheck(EntityCheck):

    def before_start(self, *args, **kwargs):
        super().before_start(*args, **kwargs)
        services.set_company_check_status(self.session, True)
        self.session.commit()

    def after_return(self, *args, **kwargs):
        services.set_company_check_status(self.session, False)
        super().after_return(*args, **kwargs)


@app.task(base=ContactCheck, bind=True)
def test_task(self):
    time.sleep(15)
    return self._number


@app.task
def background_request(request_data):
    amocrm = get_amocrm_from_first_integration()
    with Session(engine) as session:
        contact_manager = ContactManager(amocrm, session)
        company_manager = CompanyManager(amocrm, session)

        handler = HookHandler(contact_manager, company_manager, amocrm)
        handler.handle(request_data)
        handler._company_manager.set_many_fields()
        handler._contact_manager_manager.set_many_fields()
        session.commit()


@app.task(base=ContactCheck, bind=True)
def contact_check(self):
    contact_manager = ContactManager(self.amocrm, self.session)
    contact_manager.run_check()
    # self.session.commit()


@app.task(base=CompanyCheck, bind=True)
def company_check(self):
    company_manager = CompanyManager(self.amocrm, self.session)
    company_manager.run_check()
    # self.session.commit()
