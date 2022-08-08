from app.app_settings import get_settings
from datetime import datetime, timedelta
from typing import Union, List, Generator, Tuple
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


def get_lead_path(link) -> str:
    """Из ссылки на сделку получить путь к ней -> api/v4/leads/234234"""

    return link[link.find("api"):link.find("?")]


def get_lead_id(link) -> int:
    """Из пути к сделке получить ее id"""

    path = get_lead_path(link)
    return path[-(path[::-1].find("/")):]


def check_lead_younger_than(lead: dict, months: int) -> bool:
    """Проверить, что количество месяцев с момента создания сделки меньше months"""

    created_at = lead["created_at"]
    date = datetime.fromtimestamp(created_at)
    if datetime.now() - date > timedelta(days=int(months)*30):
        return False
    return True


def check_lead_is_in_success_stage(lead: dict) -> bool:
    """Проверить, что сделка находится в разделе Продажа на этапе Закрыто, оплата получена"""
    settings = get_settings()

    if lead["status_id"] == settings.success_stage_id and lead["pipeline_id"] == settings.pipeline_id:
        return True
    return False


def check_lead_is_active(lead: dict) -> bool:
    """Проверить, что сделка активна"""

    settings = get_settings()

    logger.info(
        f"Status id: {lead['status_id']}, inactive_stage_ids: {settings.inactive_stage_ids}")

    if lead["status_id"] not in settings.inactive_stage_ids:
        return True
    return False


def check_lead_is_fully_paid(lead: dict) -> Union[int, None]:
    """Проверить, что сделка полностью оплачена"""

    settings = get_settings()

    price = lead["price"]
    try:
        for field in lead["custom_fields_values"]:
            if field["field_id"] == settings.lead_paid_field:
                if int(field["values"][0]["value"]) == int(price):
                    return int(price)
        return None
    except TypeError:
        return None


def make_patch_request_data(field_id, value) -> dict:
    """Сформировать дату для patch запроса"""

    data = {
        "custom_fields_values": [{
            "field_id": field_id,
            "values": [
                {
                    "value": value
                }
            ]
        }]
    }

    return data


def make_many_patch_request_data(entries: List[dict]) -> List[dict]:
    """Сформировать дату для patch запроса для нескольких сущностей"""

    data = []
    for entry in entries:
        entry_data = {"id": entry["id"]}
        entry_data.update(make_patch_request_data(
            entry["field_id"], entry["value"]))
        data.append(entry_data)
    return data


def get_value_and_label_from_list(items: List) -> List[dict]:
    """Получить value и label для кастомных полей сущности"""

    result = []
    for item in items:
        id_and_name = {"value": str(item["id"]), "label": item["name"]}
        result.append(id_and_name)
    return result


def get_fields_from_many(fields: Generator, field_type: str) -> List[dict]:
    """Возвращает все поля определенного типа (numeric, text, etc.)"""

    fields_of_type = [
        field for field in fields if field["type"] == field_type]
    return fields_of_type


def get_success_and_active_leads(lead_manager, months, leads) -> Tuple[List[dict], List[int], Union[int, None]]:
    """Получить успешные и активные сделки"""

    success_leads = []
    active_leads = []
    for lead in leads:
        lead_id = get_lead_id(lead["_links"]["self"]["href"])
        lead_data = lead_manager.get_one(lead_id)
        if check_lead_is_in_success_stage(lead_data) and check_lead_younger_than(lead_data, months):
            success_leads.append(lead_data["price"])
        elif check_lead_is_active(lead_data):
            active_leads.append(lead_data["id"])
    return success_leads, active_leads


def get_lead_id_from_data(data) -> int:
    """Получить id сделки из даты сущности"""

    lead_id = list(data["leads"].items())[0][1][0]["id"]
    return int(lead_id)


def get_lead_main_contact_id(lead) -> int:
    """Получить id основного контакта сделки"""

    contacts = lead["_embedded"]["contacts"]
    for contact in contacts:
        if contact["is_main"]:
            return int(contact["id"])
