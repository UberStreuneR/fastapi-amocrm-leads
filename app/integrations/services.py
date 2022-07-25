from typing import List, Union
from amocrm import AmoCRM
from integrations.schemas import IntegrationInstall, Integration, IntegrationUpdate
from sqlmodel import Session
from settings_ import settings


def get_integration(session: Session, client_id: str) -> Union[Integration, None]:
    """Получить интеграцию по client_id, если нет - None"""
    return session.query(Integration).get(client_id)


def get_integrations(session: Session) -> List[Integration]:
    return session.query(Integration).all()


def get_first_integration(session: Session) -> Integration:
    return session.query(Integration).first()


def install_integration(session: Session, data: IntegrationInstall) -> Integration:
    """Установить интеграцию и пройти авторизацию через authorization_code"""
    if (integration := get_integration(session, data.client_id)) is None:
        integration = Integration.create(session, **data.dict())

    amocrm = make_amocrm(session, integration)
    amocrm.authorize("authorization_code", data.auth_code)

    return integration


def update_integration(session: Session, integration: Integration, data: IntegrationUpdate):
    """Обновить интеграцию"""
    integration.update(session, **data.dict())


def delete_integration(session: Session, client_id: str):
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
        instance.set_pipeline_id()
        instance.set_success_stage_id()
        instance.set_inactive_stage_ids()
        print(instance.create_hook())

    return AmoCRM(
        account=integration.account,
        client_id=integration.client_id,
        client_secret=settings.client_secret,
        redirect_url=f"https://{settings.app_host}/integrations/install/",
        access_token=integration.access_token,
        refresh_token=integration.refresh_token,
        on_auth=on_auth_handler,
    )
