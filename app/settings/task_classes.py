from app.worker import app
from app.integrations.deps import get_amocrm_from_first_integration
from app.database import get_session
from . import services
from app.amocrm.managers import ContactManager, CompanyManager, LeadManager


class EntityCheck(app.Task):
    """Базовый класс для пре-настройки проверок сущностей"""

    def before_start(self, *args, **kwargs) -> None:
        """Запускается до начала работы таска Celery"""

        self.session = next(get_session())
        self.amocrm = get_amocrm_from_first_integration()
        self.lead_manager = LeadManager(self.amocrm, self.session)

    def after_return(self, *args, **kwargs) -> None:
        """Запускается после окончания работы таска Celery"""

        self.session.commit()
        self.session.close()


class ContactCheckTask(EntityCheck):
    """Класс для пре-настройки проверок контактов"""

    def before_start(self, *args, **kwargs) -> None:
        super().before_start(*args, **kwargs)
        services.set_contact_check_status(self.session, True)
        self.manager = ContactManager(self.amocrm, self.session)
        self.session.commit()

    def after_return(self, *args, **kwargs) -> None:
        services.set_contact_check_status(self.session, False)
        super().after_return(*args, **kwargs)


class CompanyCheckTask(EntityCheck):
    """Класс для пре-настройки проверок компаний"""

    def before_start(self, *args, **kwargs) -> None:
        super().before_start(*args, **kwargs)
        services.set_company_check_status(self.session, True)
        self.manager = CompanyManager(self.amocrm, self.session)
        self.session.commit()

    def after_return(self, *args, **kwargs) -> None:
        services.set_company_check_status(self.session, False)
        super().after_return(*args, **kwargs)
