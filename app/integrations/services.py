from app.amocrm.base import AmoCRM
from app.amocrm.settings import SettingsSetter
from .schemas import IntegrationInstall, Integration, IntegrationUpdate
from app.app_settings import settings

from sqlmodel import Session

from typing import List, Union


def get_integration(session: Session, client_id: str) -> Union[Integration, None]:
    """Получить интеграцию по client_id, если нет - None"""

    return session.query(Integration).get(client_id)


def get_integrations(session: Session) -> List[Integration]:
    """Получить все интеграции"""

    return session.query(Integration).all()


def get_first_integration(session: Session) -> Integration:
    """Получить первую интеграцию"""

    return session.query(Integration).first()


def install_integration(session: Session, data: IntegrationInstall) -> Integration:
    """Установить интеграцию и пройти авторизацию через authorization_code"""

    if (integration := get_integration(session, data.client_id)) is None:
        integration = Integration.create(session, **data.dict())

    amocrm = make_amocrm(session, integration)
    amocrm.authorize("authorization_code", data.auth_code)

    return integration


def update_integration(session: Session, integration: Integration, data: IntegrationUpdate) -> None:
    """Обновить интеграцию"""

    integration.update(session, **data.dict())


def delete_integration(session: Session, client_id: str) -> None:
    """Удалить интеграцию"""

    session.query(Integration).where(
        Integration.client_id == client_id).delete()
    session.flush()


def make_amocrm(session: Session, integration: Integration) -> AmoCRM:
    """Создать инстанс AmoCRM для интеграции с хуком на обновление токенов"""

    def on_auth_handler(client_id: str, access_token: str, refresh_token: str, instance: AmoCRM):
        data = IntegrationUpdate(
            access_token=access_token, refresh_token=refresh_token)
        update_integration(session, integration, data)
        SettingsSetter(instance)
        # settings_setter.set_pipeline_id()
        # settings_setter.set_success_stage_id()
        # settings_setter.set_inactive_stage_ids()
        instance.create_hook()
        session.commit()

    return AmoCRM(
        account=integration.account,
        client_id=integration.client_id,
        client_secret=settings.client_secret,
        redirect_url=f"{settings.app_host}integrations/install/",
        access_token=integration.access_token,
        refresh_token=integration.refresh_token,
        on_auth=on_auth_handler,
    )
