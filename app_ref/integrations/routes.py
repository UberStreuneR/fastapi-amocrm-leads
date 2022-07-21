from fastapi import APIRouter, Depends, Query
from amocrm import AmoCRM
from integrations.deps import get_amocrm, get_logger
from database import get_session
from sqlmodel import Session
from integrations.schemas import IntegrationInstall
from integrations import services

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/install/")
def install_integration(
    session: Session = Depends(get_session),
    code: str = Query(),
    referer: str = Query(),
    client_id: str = Query(),
):
    """Эндпоинт для установки интеграции"""
    # logger.info("INSTALL_INTEGRATION path called")
    account = referer.split(".", 1)[0]
    data = IntegrationInstall(
        client_id=client_id, account=account, auth_code=code)
    # logger.info("Calling install_integration")
    services.install_integration(session, data)
    # logger.info("Called install_integration")


@router.get("/uninstall/")
def uninstall_integration(session: Session = Depends(get_session), client_uuid: str = Query()):
    """Эндпоинт для удаления интеграции"""

    services.delete_integration(session, client_uuid)


@router.get("/get")
def get_integrations(session: Session = Depends(get_session)):
    data = {
        "integrations": services.get_integrations(session),
    }
    return data
