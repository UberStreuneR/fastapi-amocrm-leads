from fastapi import APIRouter, Depends, Query
from app.database import get_session
from sqlmodel import Session
from app.integrations.schemas import IntegrationInstall, IntegrationUpdate
from app.integrations import services

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/install/")
def install_integration(
    session: Session = Depends(get_session),
    code: str = Query(),
    referer: str = Query(),
    client_id: str = Query(),
):
    """Эндпоинт для установки интеграции"""
    account = referer.split(".", 1)[0]
    data = IntegrationInstall(
        client_id=client_id, account=account, auth_code=code)
    services.install_integration(session, data)


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


@router.get("/get-first")
def get_first_integration(session: Session = Depends(get_session)):
    return services.get_first_integration(session)


# @router.post("/corrupt-integration")
# def corrupt(session: Session = Depends(get_session)):
#     integration = services.get_first_integration(session)
#     update = IntegrationUpdate(
#         access_token="some-corrupted-value", refresh_token=integration.refresh_token)
#     integration.update(session, **update.dict())
#     session.commit()
