from app.worker import app
from app.integrations.deps import get_amocrm_from_first_integration
from app.settings.utils import ContactManager, CompanyManager, HookHandler
from app.database import get_session
from app.settings import services


class EntityCheck(app.Task):

    def before_start(self, *args, **kwargs):
        self.session = next(get_session())
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


@app.task
def background_request(request_data):
    amocrm = get_amocrm_from_first_integration()
    session = next(get_session())
    contact_manager = ContactManager(amocrm, session)
    company_manager = CompanyManager(amocrm, session)

    handler = HookHandler(contact_manager, company_manager, amocrm)
    handler.handle(request_data)


@app.task(base=ContactCheck, bind=True)
def contact_check(self):
    contact_manager = ContactManager(self.amocrm, self.session)
    contact_manager.run_check()


@app.task(base=CompanyCheck, bind=True)
def company_check(self):
    company_manager = CompanyManager(self.amocrm, self.session)
    company_manager.run_check()
