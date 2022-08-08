from app.database import DatabaseModel
from pydantic import BaseModel
from sqlmodel import Field
from typing import Optional, List


class StatusSetting(DatabaseModel, BaseModel, table=True):
    """Позиция в таблице в Статус клиента"""

    id: Optional[int] = Field(default=None, primary_key=True)
    status: str
    dependency_type: str  # quantity | sum
    entity_type: str  # company | contact
    field_id: int
    from_amount: Optional[int] = Field(default=None)
    to_amount: int


class BaseSetting(BaseModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    months: int
    lead_field_id: int


class ContactSetting(DatabaseModel, BaseSetting, table=True):
    """Настройки на вкладке Количество сделок у контакта"""

    contact_field_id: int


class CompanySetting(DatabaseModel, BaseSetting, table=True):
    """Настройки на вкладке Количество сделок у контакта"""

    company_field_id: int


class ContactCheckStatus(DatabaseModel, BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    running: bool = False


class CompanyCheckStatus(DatabaseModel, BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    running: bool = False


class UpdateStageIds(BaseModel):
    pipeline_id: Optional[int] = None
    success_stage_id: Optional[int] = None
    inactive_stage_ids: Optional[List[int]] = None


class StageIds(DatabaseModel, UpdateStageIds, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
