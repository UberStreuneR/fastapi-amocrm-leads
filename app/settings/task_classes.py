from app.worker import app
from app.integrations.deps import get_amocrm_from_first_integration
from app.database import get_session
from . import services


class EntityCheck(app.Task):

    def before_start(self, *args, **kwargs) -> None:
        self.session = next(get_session())
        self.amocrm = get_amocrm_from_first_integration()

    def after_return(self, *args, **kwargs) -> None:
        self.session.commit()


class ContactCheck(EntityCheck):

    def before_start(self, *args, **kwargs) -> None:
        super().before_start(*args, **kwargs)
        services.set_contact_check_status(self.session, True)
        self.session.commit()

    def after_return(self, *args, **kwargs) -> None:
        services.set_contact_check_status(self.session, False)
        super().after_return(*args, **kwargs)


class CompanyCheck(EntityCheck):

    def before_start(self, *args, **kwargs) -> None:
        super().before_start(*args, **kwargs)
        services.set_company_check_status(self.session, True)
        self.session.commit()

    def after_return(self, *args, **kwargs) -> None:
        services.set_company_check_status(self.session, False)
        super().after_return(*args, **kwargs)
