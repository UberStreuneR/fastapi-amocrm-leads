from app.amocrm.base import AmoCRM
from app.settings.schemas import UpdateStageIds
from . import services
from sqlmodel import Session
from typing import List


class StageIdsSetter:
    """Класс для установки настроек приложения"""

    def __init__(self, amocrm: AmoCRM, session: Session) -> None:
        self.amocrm = amocrm
        self.session = session
        self.stage_ids = services.get_stage_ids(session)

    def get_pipeline_id(self) -> int:
        """Получить id воронки Продажа"""

        if self.stage_ids.pipeline_id is None:
            response = self.amocrm.make_request(
                "get", "api/v4/leads/pipelines")
            for pipeline in response["_embedded"]["pipelines"]:
                if pipeline["name"] == "Продажа":
                    self.stage_ids.pipeline_id = pipeline["id"]
                    self.session.flush()
                    return

    def get_success_stage_id(self) -> int:
        """Получить id этапа Закрыто, оплата получена"""

        if self.stage_ids.success_stage_id is None:
            response = self.amocrm.make_request(
                "get", f"api/v4/leads/pipelines/{self.stage_ids.pipeline_id}")
            for status in response["_embedded"]["statuses"]:
                if status["name"] == "Закрыто. Оплата получена":
                    self.stage_ids.success_stage_id = status["id"]
                    self.session.flush()
                    return

    def get_inactive_stage_ids(self) -> List[int]:
        """Получить ids неактивных этапов"""

        inactive_statuses = []
        if self.stage_ids.inactive_stage_ids is None:
            response = self.amocrm.make_request(
                "get", "api/v4/leads/pipelines")
            for pipeline in response["_embedded"]["pipelines"]:
                for status in pipeline["_embedded"]["statuses"]:
                    if not status["is_editable"] and not status['id'] in inactive_statuses:
                        inactive_statuses.append(status["id"])
        self.stage_ids.inactive_stage_ids = inactive_statuses
        self.session.flush()

    def set_ids(self) -> None:
        self.get_pipeline_id()
        self.get_success_stage_id()
        self.get_inactive_stage_ids()
        self.session.commit()
        # update_data = UpdateStageIds(
        #     pipeline_id, success_stage_id, inactive_stage_ids)
        # services.set_stage_ids(self.session, update_data)
