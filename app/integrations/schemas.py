from pydantic import BaseModel
from sqlmodel import Field

from app.database import DatabaseModel


class IntegrationBase(BaseModel):
    """Базовая схема интеграции"""

    client_id: str = Field(primary_key=True)
    account: str


class Integration(DatabaseModel, IntegrationBase, table=True):
    """Модель интеграции"""

    access_token: str = None
    refresh_token: str = None


class IntegrationInstall(IntegrationBase):
    """Схема установки интеграции"""

    auth_code: str


class IntegrationUpdate(BaseModel):
    """Схема обновления интеграции"""

    access_token: str
    refresh_token: str
