from fastapi import HTTPException, Depends
from jose import jwt, JWTError
from sqlmodel import Session
from starlette import status
from starlette.requests import Request
from app.amocrm import AmoCRM
from app.database import get_session
from . import services
from .schemas import Integration
from app.settings_ import settings

import logging
import sys


def get_auth_data(request: Request) -> dict:
    """Получить авторизационные данные из jwt токена в x-auth-token"""

    if (auth_token := request.headers.get("x-auth-token")) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        return jwt.decode(
            auth_token,
            settings.client_secret,
            algorithms=["HS256"],
            options={"verify_aud": False, "verify_nbf": False},
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def get_integration(
    session: Session = Depends(get_session),
    auth_data: dict = Depends(get_auth_data),
) -> Integration:
    """Получить интеграцию по client_uuid из x-auth-token, если нет - вернуть 401"""
    if (integration := services.get_integration(session, auth_data["client_uuid"])) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return integration


def get_amocrm(
    session: Session = Depends(get_session),
    integration: Integration = Depends(get_integration),
) -> AmoCRM:
    """Создать инстанс AmoCRM по интеграции из x-auth-token"""
    return services.make_amocrm(session, integration)


def get_amocrm_from_first_integration():
    session = next(get_session())
    integration = services.get_first_integration(session)
    if integration is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return services.make_amocrm(session, integration)


def get_logger():
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
        level=logging.DEBUG,
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    logger = logging.getLogger("Sockets")
    logging.getLogger("chardet.charsetprober").disabled = True
    return logger
