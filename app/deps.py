from fastapi import HTTPException, Depends
from starlette import status
from starlette.requests import Request
from settings import settings
from jose import jwt, JWTError
from logger import logger


def get_auth_data(request: Request) -> dict:
    """Получить авторизационные данные из jwt токена в x-auth-token"""

    if (auth_token := request.headers.get("x-auth-token")) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    # logger.info(f"AUTH_TOKEN\n{auth_token}")
    try:
        return jwt.decode(
            auth_token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_aud": False, "verify_nbf": False},
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
