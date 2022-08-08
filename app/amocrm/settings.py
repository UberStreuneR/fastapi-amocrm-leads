from app.amocrm.base import AmoCRM
from app.app_settings import get_settings


class SettingsSetter:
    """Класс для установки настроек приложения"""

    def __init__(self, amocrm: AmoCRM) -> None:
        self.amocrm = amocrm
        self.settings = get_settings()
        self.set_pipeline_id()
        self.set_success_stage_id()
        self.set_inactive_stage_ids()

    def set_pipeline_id(self) -> None:
        """Установить id воронки Продажа"""

        if self.settings.pipeline_id is None:
            response = self.amocrm.make_request(
                "get", "api/v4/leads/pipelines")
            for pipeline in response["_embedded"]["pipelines"]:
                if pipeline["name"] == "Продажа":
                    self.settings.pipeline_id = pipeline["id"]
                    break

    def set_success_stage_id(self) -> None:
        """Установить id этапа Закрыто, оплата получена"""

        if self.settings.success_stage_id is None:
            response = self.amocrm.make_request(
                "get", f"api/v4/leads/pipelines/{self.settings.pipeline_id}")
            for status in response["_embedded"]["statuses"]:
                if status["name"] == "Закрыто. Оплата получена":
                    self.settings.success_stage_id = status["id"]
                    break

    def set_inactive_stage_ids(self) -> None:
        """Установить ids неактивных этапов"""

        inactive_statuses = []
        if self.settings.inactive_stage_ids is None:
            response = self.amocrm.make_request(
                "get", "api/v4/leads/pipelines")
            for pipeline in response["_embedded"]["pipelines"]:
                for status in pipeline["_embedded"]["statuses"]:
                    if not status["is_editable"] and not status['id'] in inactive_statuses:
                        inactive_statuses.append(status["id"])
        self.settings.inactive_stage_ids = inactive_statuses
