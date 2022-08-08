from app.amocrm.base import AmoCRM
from app.app_settings import settings


class SettingsSetter:
    """Класс для установки настроек приложения"""

    def __init__(self, amocrm: AmoCRM) -> None:
        self.amocrm = amocrm

    def set_pipeline_id(self) -> None:
        """Установить id воронки Продажа"""

        if settings.pipeline_id is None:
            response = self.amocrm.make_request(
                "get", "api/v4/leads/pipelines")
            for pipeline in response["_embedded"]["pipelines"]:
                if pipeline["name"] == "Продажа":
                    settings.pipeline_id = pipeline["id"]
                    break

    def set_success_stage_id(self) -> None:
        """Установить id этапа Закрыто, оплата получена"""

        if settings.success_stage_id is None:
            response = self.amocrm.make_request(
                "get", f"api/v4/leads/pipelines/{settings.pipeline_id}")
            for status in response["_embedded"]["statuses"]:
                if status["name"] == "Закрыто. Оплата получена":
                    settings.success_stage_id = status["id"]
                    break

    def set_inactive_stage_ids(self) -> None:
        """Установить ids неактивных этапов"""

        inactive_statuses = []
        if settings.inactive_stage_ids is None:
            response = self.amocrm.make_request(
                "get", "api/v4/leads/pipelines")
            for pipeline in response["_embedded"]["pipelines"]:
                for status in pipeline["_embedded"]["statuses"]:
                    if not status["is_editable"]:
                        inactive_statuses.append(status["id"])
        settings.inactive_stage_ids = inactive_statuses
