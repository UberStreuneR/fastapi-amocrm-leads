from ast import Str
from pydantic import BaseModel
from database import DatabaseModel
from typing import Union, Optional
from sqlmodel import Field


class StatusSetting(DatabaseModel, BaseModel, table=True):
    """Позиция в таблице в Статус клиента"""

    id: Optional[int] = Field(default=None, primary_key=True)
    status: str
    dependency_type: str  # quantity | sum
    entity_type: str  # company | contact
    field_id: str
    from_amount: int
    to_amount: int


class BaseSetting(BaseModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    months: int
    lead_field_id: str


class ContactSetting(DatabaseModel, BaseSetting, table=True):
    """Настройки на вкладке Количество сделок у контакта"""

    contact_field_id: str


class CompanySetting(DatabaseModel, BaseSetting, table=True):
    """Настройки на вкладке Количество сделок у контакта"""

    company_field_id: str
