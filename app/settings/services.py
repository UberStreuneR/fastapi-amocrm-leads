from .schemas import StatusSetting, ContactSetting, CompanySetting, ContactCheckStatus, CompanyCheckStatus, StageIds, UpdateStageIds
from sqlmodel import Session
from typing import List


def get_status_settings(session: Session) -> List[StatusSetting]:
    """Получить настройки Статуса клиента"""
    return session.query(StatusSetting).all()


def get_status_settings_for_company(session: Session) -> List[StatusSetting]:
    """Получить настройки статуса клиента для компании"""

    return session.query(StatusSetting).where(StatusSetting.entity_type == "company").all()


def get_status_settings_for_contact(session: Session) -> List[StatusSetting]:
    """Получить настройки статуса клиента для контакта"""

    return session.query(StatusSetting).where(StatusSetting.entity_type == "contact").all()


def save_status_settings(session: Session, status_settings: List[StatusSetting]) -> List[StatusSetting]:
    """Сохранить настройки статуса клиента"""

    delete_status_settings(session)
    result = []
    for status_setting in status_settings:
        result.append(StatusSetting.create(session, **status_setting.dict()))
    return result


def delete_status_settings(session: Session) -> None:
    """Удалить настройки статуса клиента"""

    instances = session.query(StatusSetting).all()
    for instance in instances:
        session.delete(instance)


def get_contact_setting(session: Session) -> ContactSetting:
    """Получить настройки для контакта"""

    return session.query(ContactSetting).first()


def set_contact_setting(session: Session, contact_setting: ContactSetting) -> ContactSetting:
    """Установить настройки для контакта"""

    instance = session.query(ContactSetting).first()
    if instance is None:
        instance = ContactSetting.create(session, **contact_setting.dict())
    else:
        data = contact_setting.dict()
        data.update({"id": instance.id})
        instance.update(session, **data)
    return instance


def get_company_setting(session: Session) -> CompanySetting:
    """Получить настройки для компании"""

    return session.query(CompanySetting).first()


def set_company_setting(session: Session, company_setting: CompanySetting) -> CompanySetting:
    """Установить настройки компании"""

    instance = session.query(CompanySetting).first()
    if instance is None:
        instance = CompanySetting.create(session, **company_setting.dict())
    else:
        data = company_setting.dict()
        data.update({"id": instance.id})
        instance.update(session, **data)
    return instance


def set_contact_check_status(session: Session, running: bool) -> ContactCheckStatus:
    """Установить статус проверки контакта"""

    instance = session.query(ContactCheckStatus).first()
    if instance is None:
        instance = ContactCheckStatus.create(session, running=running)
    else:
        instance.update(session, running=running)
    return instance


def get_contact_check_status(session: Session) -> bool:
    """Получить статус проверки контакта"""

    instance = session.query(ContactCheckStatus).first()
    if instance is None:
        return False
    return instance.running


def set_company_check_status(session: Session, running: bool) -> CompanyCheckStatus:
    """Установить статус проверки компании"""

    instance = session.query(CompanyCheckStatus).first()
    if instance is None:
        instance = CompanyCheckStatus.create(session, running=running)
    else:
        instance.update(session, running=running)
    return instance


def get_company_check_status(session: Session) -> bool:
    """Получить статус проверки компании"""

    instance = session.query(CompanyCheckStatus).first()
    if instance is None:
        return False
    return instance.running


def get_stage_ids(session: Session) -> StageIds:
    """Получить объект id стадий и воронок"""

    instance = session.query(StageIds).first()
    if instance is None:
        return StageIds.create(session)
    return instance


def set_stage_ids(session: Session, update_data: UpdateStageIds) -> StageIds:
    """Получить объект id стадий и воронок"""

    instance = session.query(StageIds).first()
    if instance is None:
        return StageIds.create(session, **update_data.dict())
    instance.update(session, **update_data.dict())
    return instance
