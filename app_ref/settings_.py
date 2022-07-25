from pydantic import BaseSettings, PostgresDsn
from typing import List


class Settings(BaseSettings):

    database: PostgresDsn
    app_host: str
    client_secret: str
    pipeline_id: int = None
    success_stage_id: int = None
    inactive_stage_ids: List[int] = None


settings = Settings()
